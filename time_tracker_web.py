from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, request, redirect, url_for, render_template_string, send_file

app = Flask(__name__)

LOG_FILE = Path("time_log.csv")

# ---------- Data layer ----------

def load_log() -> pd.DataFrame:
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE)
    else:
        return pd.DataFrame(columns=["date", "time", "type", "comment"])


def save_log(df: pd.DataFrame) -> None:
    df.to_csv(LOG_FILE, index=False)


def add_entry(entry_type: str, comment: str = "") -> None:
    now = datetime.now()
    df = load_log()
    new_row = {
        "date": now.date().isoformat(),
        "time": now.time().strftime("%H:%M:%S"),
        "type": entry_type.upper(),
        "comment": comment,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_log(df)


def export_month(year: int, month: int) -> Path:
    df = load_log()
    if df.empty:
        raise ValueError("No records yet.")

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    filtered = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]

    if filtered.empty:
        raise ValueError("No records for this month.")

    filtered = filtered.sort_values(by=["date", "time"])
    output_name = Path(f"timesheet_{year:04d}-{month:02d}.xlsx")
    filtered.to_excel(output_name, index=False)
    return output_name


# ---------- HTML template (simple nice UI) ----------

PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Time Tracker</title>
  <!-- Bootstrap via CDN for a nicer look -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: #f4f6f9;
    }
    .card {
      border-radius: 1rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .btn-checkin {
      font-weight: 600;
    }
    .btn-checkout {
      font-weight: 600;
    }
    .table thead {
      background-color: #0d6efd;
      color: white;
    }
  </style>
</head>
<body>
<div class="container py-4">
  <h1 class="mb-4 text-center">⏱️ Simple Time Tracker</h1>

  {% if message %}
    <div class="alert alert-info">{{ message }}</div>
  {% endif %}

  <div class="row g-4">
    <!-- Check-in / Check-out -->
    <div class="col-md-6">
      <div class="card p-3">
        <h4>Register time</h4>
        <form method="post" action="{{ url_for('check') }}" class="mt-3">
          <div class="mb-3">
            <label for="comment" class="form-label">Comment (optional)</label>
            <input type="text" id="comment" name="comment" class="form-control" placeholder="Example: Arrive at work">
          </div>
          <div class="d-flex gap-2">
            <button name="type" value="IN" class="btn btn-success btn-checkin w-50">Check IN</button>
            <button name="type" value="OUT" class="btn btn-danger btn-checkout w-50">Check OUT</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Export month -->
    <div class="col-md-6">
      <div class="card p-3">
        <h4>Export month to Excel</h4>
        <form method="post" action="{{ url_for('export_month_route') }}" class="mt-3">
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label for="year" class="form-label">Year</label>
              <input type="number" id="year" name="year" class="form-control" value="{{ current_year }}">
            </div>
            <div class="col-6">
              <label for="month" class="form-label">Month</label>
              <input type="number" id="month" name="month" class="form-control" value="{{ current_month }}" min="1" max="12">
            </div>
          </div>
          <button class="btn btn-primary w-100">Export & download</button>
        </form>
      </div>
    </div>
  </div>

  <!-- Table with latest records -->
  <div class="card mt-4 p-3">
    <h4>Latest records</h4>
    {% if log.empty %}
      <p class="mt-2 text-muted">No records yet.</p>
    {% else %}
      <div class="table-responsive mt-2">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Type</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            {% for _, row in log.iterrows() %}
              <tr>
                <td>{{ row["date"] }}</td>
                <td>{{ row["time"] }}</td>
                <td>
                  {% if row["type"] == "IN" %}
                    <span class="badge bg-success">IN</span>
                  {% else %}
                    <span class="badge bg-danger">OUT</span>
                  {% endif %}
                </td>
                <td>{{ row["comment"] }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% endif %}
  </div>
</div>
</body>
</html>
"""


# ---------- Routes ----------

@app.route("/")
def index():
    df = load_log()
    message = request.args.get("msg", "")
    now = datetime.now()
    return render_template_string(
        PAGE_TEMPLATE,
        log=df,
        message=message,
        current_year=now.year,
        current_month=now.month,
    )


@app.route("/check", methods=["POST"])
def check():
    entry_type = request.form.get("type", "IN")
    comment = request.form.get("comment", "")
    if entry_type not in ("IN", "OUT"):
        entry_type = "IN"
    add_entry(entry_type, comment)
    msg = f"Registered {entry_type} successfully."
    return redirect(url_for("index", msg=msg))


@app.route("/export", methods=["POST"])
def export_month_route():
    try:
        year = int(request.form["year"])
        month = int(request.form["month"])
        output_path = export_month(year, month)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return redirect(url_for("index", msg=str(e)))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

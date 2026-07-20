"""
data_analysis.py

Demonstrates logging common data-analysis output with Logduo.

Covers:
- saving a CSV file to the Logduo output directory
- reading the CSV file with pandas
- logging DataFrame previews and summary statistics
- logging statsmodels regression output when installed
- saving a matplotlib plot to the Logduo output directory

Optional example dependencies:
    pip install pandas numpy matplotlib statsmodels

Last edited: 2026-07-08
"""

from pathlib import Path

from logduo import log

LOG_DIR = Path.cwd() / "logs"


def section(title: str) -> None:
    log("")
    log("=" * 87)
    log(title)
    log("=" * 87)


def main() -> None:  # noqa: PLR0915   # example scripts can have 'too many statements'
    log.configure(
        log_dir_path=LOG_DIR,
        console_wrap_width=100,
        log_wrap_width=120,
    )

    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
    except ImportError:
        log("Data-analysis example skipped: optional packages are not installed.")
        log("Install optional example dependencies with:")
        log("    pip install pandas numpy matplotlib statsmodels")
        log.close()
        return

    assert log.output_dir_path is not None

    # ------------------------------------------------------------------
    section("Create and save a small CSV file")

    rng = np.random.default_rng(42)
    observations = 40

    education = rng.integers(10, 21, observations)
    experience = rng.integers(0, 31, observations)
    error = rng.normal(0, 4_000, observations)

    income = (
        12_000
        + 3_000 * education
        + 750 * experience
        + error
    )

    data = pd.DataFrame(
        {
            "income": income.round(2),
            "education": education,
            "experience": experience,
        }
    )

    csv_path = log.output_dir_path / "example_econometrics_data.csv"
    data.to_csv(csv_path, index=False)

    log(f"CSV file saved to: {csv_path}")

    # ------------------------------------------------------------------
    section("Read the CSV file and log data previews")

    data = pd.read_csv(csv_path)  # noqa inspection PyArgumentList

    log("First 8 rows")
    log(data.head(8).to_string(index=False))

    log("Last 8 rows")
    log(data.tail(8).to_string(index=False))

    # ------------------------------------------------------------------
    section("Summary statistics")

    log("Descriptive statistics")
    log(data.describe().round(2).to_string())

    log("Correlation matrix")
    log(data.corr(numeric_only=True).round(3).to_string())

    # ------------------------------------------------------------------
    section("Regression output")

    try:
        import statsmodels.api as sm  # noqa # sm not defined in except
    except ImportError:
        log("Regression example skipped: statsmodels is not installed.")
        log("Install with: pip install statsmodels")
    else:
        x = data[["education", "experience"]]
        x = sm.add_constant(x)

        y = data["income"]

        model = sm.OLS(y, x)
        results = model.fit()

        log("OLS regression results")
        log(results.summary().as_text())

        log("Selected regression values")
        log(f"R-squared: {results.rsquared:.4f}")

        observation_count = int(float(results.nobs))     # noqa  # statsmodels typing incorrectly reports nobs as callable
        education_coefficient = float(results.params["education"])
        experience_coefficient = float(results.params["experience"])

        log(f"Observations: {observation_count}")
        log(f"Education coefficient: {education_coefficient:.2f}")
        log(f"Experience coefficient: {experience_coefficient:.2f}")


    # ------------------------------------------------------------------
    section("Save a basic plot to the Logduo output directory")

    fig, ax = plt.subplots()
    ax.scatter(data["education"], data["income"])
    ax.set_xlabel("Education")
    ax.set_ylabel("Income")
    ax.set_title("Example data: income by education")
    plot_path = log.output_dir_path / "income_by_education.png"
    fig.savefig(plot_path)
    plt.close(fig)

    log(f"Plot saved to: {plot_path}")
    log(
        "Example logging a matplotlib figure object "
        f"(placeholder only; does not convert to image): {fig}"
    )

    log.close()


if __name__ == "__main__":
    main()

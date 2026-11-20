from app.planner import plan_observations


def test_plan_returns_all_registered_sites():
    result = plan_observations(
        ra_deg=180,
        dec_deg=20,
        start_time="2026-11-05T00:00:00",
        duration_hours=6,
        cadence_minutes=30,
        require_astronomical_darkness=False,
    )
    assert len(result["results"]) == 3
    assert all("observable" in row for row in result["results"])


def test_invalid_declination_is_rejected():
    try:
        plan_observations(
            ra_deg=180,
            dec_deg=95,
            start_time="2026-11-05T00:00:00",
        )
    except ValueError as exc:
        assert "dec_deg" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid declination")

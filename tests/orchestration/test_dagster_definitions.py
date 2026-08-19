from skill_observatory.orchestration.dagster.definitions import defs


def test_dagster_definitions_load_expected_assets() -> None:
    asset_keys = {
        key.to_user_string()
        for key in defs.resolve_asset_graph().get_all_asset_keys()
    }

    assert asset_keys == {
        "historical_ads_ingestion",
        "bronze_job_ads",
        "regex_skill_mentions",
        "regex_skill_quality",
        "dbt_gold_marts",
    }
    assert defs.resolve_job_def("historical_pipeline_job") is not None

from harvesters.git.stacks import detect_stacks


def test_detect_sql_dbt_stack():
    paths = ["dbt_project.yml", "models/staging/stg_orders.sql", "schema.yml"]
    assert "sql-dbt" in detect_stacks(paths)


def test_detect_java_stack():
    paths = ["pom.xml", "src/main/java/com/inspira/sample/OrdersRepository.java"]
    assert "java" in detect_stacks(paths)


def test_detect_dotnet_stack():
    paths = ["SampleApp.sln", "SampleApp.csproj", "OrdersService.cs"]
    assert "dotnet" in detect_stacks(paths)


def test_detect_talend_stack():
    paths = ["talend.project", "jobs/load_orders.item", "jobs/load_orders.properties"]
    assert "talend" in detect_stacks(paths)


def test_detect_shell_stack():
    paths = ["scripts/deploy.sh", "scripts/setup.ps1"]
    assert "shell" in detect_stacks(paths)


def test_detect_multiple_stacks_in_one_repo():
    paths = ["pom.xml", "src/main/resources/orders.sql", "scripts/run.sh"]
    detected = detect_stacks(paths)
    assert "java" in detected
    assert "shell" in detected


def test_no_stack_detected_for_unrelated_files():
    paths = ["README.md", "LICENSE"]
    assert detect_stacks(paths) == []

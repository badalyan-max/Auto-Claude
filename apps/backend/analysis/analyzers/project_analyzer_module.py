"""
Project Analyzer Module
=======================

Analyzes entire projects, detecting monorepo structures, services, infrastructure, and conventions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import SERVICE_INDICATORS, SERVICE_ROOT_FILES, SKIP_DIRS
from .service_analyzer import ServiceAnalyzer


class ProjectAnalyzer:
    """Analyzes an entire project, detecting monorepo structure and all services."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.index = {
            "project_root": str(self.project_dir),
            "project_type": "single",  # or "monorepo"
            "services": {},
            "infrastructure": {},
            "conventions": {},
        }

    def analyze(self) -> dict[str, Any]:
        """Run full project analysis."""
        self._detect_project_type()
        self._find_and_analyze_services()
        self._analyze_infrastructure()
        self._detect_conventions()
        self._map_dependencies()
        return self.index

    def _detect_project_type(self) -> None:
        """Detect if this is a monorepo or single project."""
        monorepo_indicators = [
            "pnpm-workspace.yaml",
            "lerna.json",
            "nx.json",
            "turbo.json",
            "rush.json",
        ]

        for indicator in monorepo_indicators:
            if (self.project_dir / indicator).exists():
                self.index["project_type"] = "monorepo"
                self.index["monorepo_tool"] = indicator.replace(".json", "").replace(
                    ".yaml", ""
                )
                return

        # Check for packages/apps directories
        if (self.project_dir / "packages").exists() or (
            self.project_dir / "apps"
        ).exists():
            self.index["project_type"] = "monorepo"
            return

        # Check for multiple service directories
        service_dirs_found = 0
        for item in self.project_dir.iterdir():
            if not item.is_dir():
                continue
            if item.name in SKIP_DIRS or item.name.startswith("."):
                continue

            # Check if this directory has service root files
            if any((item / f).exists() for f in SERVICE_ROOT_FILES):
                service_dirs_found += 1

        # If we have 2+ directories with service root files, it's likely a monorepo
        if service_dirs_found >= 2:
            self.index["project_type"] = "monorepo"

    def _find_and_analyze_services(self) -> None:
        """Find all services and analyze each."""
        services = {}

        if self.index["project_type"] == "monorepo":
            # Look for services in common locations
            service_locations = [
                self.project_dir,
                self.project_dir / "packages",
                self.project_dir / "apps",
                self.project_dir / "services",
            ]

            for location in service_locations:
                if not location.exists():
                    continue

                for item in location.iterdir():
                    if not item.is_dir():
                        continue
                    if item.name in SKIP_DIRS:
                        continue
                    if item.name.startswith("."):
                        continue

                    # Check if this looks like a service
                    has_root_file = any((item / f).exists() for f in SERVICE_ROOT_FILES)
                    is_service_name = item.name.lower() in SERVICE_INDICATORS

                    if has_root_file or (
                        location == self.project_dir and is_service_name
                    ):
                        analyzer = ServiceAnalyzer(item, item.name)
                        service_info = analyzer.analyze()
                        if service_info.get(
                            "language"
                        ):  # Only include if we detected something
                            services[item.name] = service_info
        else:
            # Single project - analyze root
            analyzer = ServiceAnalyzer(self.project_dir, "main")
            service_info = analyzer.analyze()
            if service_info.get("language"):
                services["main"] = service_info

        # Check for Supabase backend (even in single projects)
        supabase_service = self._analyze_supabase()
        if supabase_service:
            services["supabase"] = supabase_service

        self.index["services"] = services

    def _analyze_supabase(self) -> dict[str, Any] | None:
        """Analyze Supabase backend-as-a-service if present."""
        supabase_dir = self.project_dir / "supabase"
        if not supabase_dir.exists():
            return None

        config_file = supabase_dir / "config.toml"
        functions_dir = supabase_dir / "functions"
        migrations_dir = supabase_dir / "migrations"

        if not config_file.exists():
            return None

        service_info: dict[str, Any] = {
            "name": "supabase",
            "path": str(supabase_dir),
            "language": "TypeScript",  # Supabase Edge Functions use Deno/TypeScript
            "framework": "Supabase",
            "type": "backend",
            "runtime": "Deno",
            "key_directories": {},
        }

        # Analyze Edge Functions
        if functions_dir.exists():
            edge_functions = []
            for func_dir in functions_dir.iterdir():
                if func_dir.is_dir() and not func_dir.name.startswith("_"):
                    # Check for index.ts file (standard Supabase function structure)
                    index_file = func_dir / "index.ts"
                    if index_file.exists():
                        edge_functions.append(func_dir.name)
                    else:
                        # Also check for other .ts files
                        ts_files = list(func_dir.glob("*.ts"))
                        if ts_files:
                            edge_functions.append(func_dir.name)

            if edge_functions:
                service_info["edge_functions"] = edge_functions
                service_info["key_directories"]["functions"] = {
                    "path": "supabase/functions",
                    "purpose": "Edge Functions (serverless backend)",
                }

        # Analyze Database Migrations
        if migrations_dir.exists():
            migrations = []
            for migration_file in sorted(migrations_dir.glob("*.sql")):
                migrations.append(migration_file.name)

            if migrations:
                service_info["migrations"] = migrations
                service_info["key_directories"]["migrations"] = {
                    "path": "supabase/migrations",
                    "purpose": "Database migrations",
                }
                service_info["has_database"] = True

        # Parse config.toml for additional info
        try:
            config_content = config_file.read_text()
            if "project_id" in config_content:
                service_info["configured"] = True
        except (OSError, UnicodeDecodeError):
            pass

        return service_info

    def _analyze_infrastructure(self) -> None:
        """Analyze infrastructure configuration."""
        infra = {}

        # Docker
        if (self.project_dir / "docker-compose.yml").exists():
            infra["docker_compose"] = "docker-compose.yml"
            compose_content = self._read_file("docker-compose.yml")
            infra["docker_services"] = self._parse_compose_services(compose_content)
        elif (self.project_dir / "docker-compose.yaml").exists():
            infra["docker_compose"] = "docker-compose.yaml"
            compose_content = self._read_file("docker-compose.yaml")
            infra["docker_services"] = self._parse_compose_services(compose_content)

        if (self.project_dir / "Dockerfile").exists():
            infra["dockerfile"] = "Dockerfile"

        # Docker directory
        docker_dir = self.project_dir / "docker"
        if docker_dir.exists():
            dockerfiles = list(docker_dir.glob("Dockerfile*")) + list(
                docker_dir.glob("*.Dockerfile")
            )
            if dockerfiles:
                infra["docker_directory"] = "docker/"
                infra["dockerfiles"] = [
                    str(f.relative_to(self.project_dir)) for f in dockerfiles
                ]

        # CI/CD
        if (self.project_dir / ".github" / "workflows").exists():
            infra["ci"] = "GitHub Actions"
            workflows = list((self.project_dir / ".github" / "workflows").glob("*.yml"))
            infra["ci_workflows"] = [f.name for f in workflows]
        elif (self.project_dir / ".gitlab-ci.yml").exists():
            infra["ci"] = "GitLab CI"
        elif (self.project_dir / ".circleci").exists():
            infra["ci"] = "CircleCI"

        # Deployment
        deployment_files = {
            "vercel.json": "Vercel",
            "netlify.toml": "Netlify",
            "fly.toml": "Fly.io",
            "render.yaml": "Render",
            "railway.json": "Railway",
            "Procfile": "Heroku",
            "app.yaml": "Google App Engine",
            "serverless.yml": "Serverless Framework",
        }

        for file, platform in deployment_files.items():
            if (self.project_dir / file).exists():
                infra["deployment"] = platform
                break

        # Supabase backend-as-a-service
        supabase_dir = self.project_dir / "supabase"
        if supabase_dir.exists() and (supabase_dir / "config.toml").exists():
            infra["backend_service"] = "Supabase"
            infra["supabase"] = {
                "config": "supabase/config.toml",
            }
            # Check for Edge Functions
            functions_dir = supabase_dir / "functions"
            if functions_dir.exists():
                functions = [
                    d.name for d in functions_dir.iterdir()
                    if d.is_dir() and not d.name.startswith("_")
                ]
                if functions:
                    infra["supabase"]["edge_functions"] = functions
            # Check for migrations
            migrations_dir = supabase_dir / "migrations"
            if migrations_dir.exists():
                infra["supabase"]["has_migrations"] = True

        self.index["infrastructure"] = infra

    def _parse_compose_services(self, content: str) -> list[str]:
        """Extract service names from docker-compose content."""
        services = []
        in_services = False
        for line in content.split("\n"):
            if line.strip() == "services:":
                in_services = True
                continue
            if in_services:
                # Service names are at 2-space indent
                if (
                    line.startswith("  ")
                    and not line.startswith("    ")
                    and line.strip().endswith(":")
                ):
                    service_name = line.strip().rstrip(":")
                    services.append(service_name)
                elif line and not line.startswith(" "):
                    break  # End of services section
        return services

    def _detect_conventions(self) -> None:
        """Detect project-wide conventions."""
        conventions = {}

        # Python linting
        if (self.project_dir / "ruff.toml").exists() or self._has_in_pyproject("ruff"):
            conventions["python_linting"] = "Ruff"
        elif (self.project_dir / ".flake8").exists():
            conventions["python_linting"] = "Flake8"
        elif (self.project_dir / "pylintrc").exists():
            conventions["python_linting"] = "Pylint"

        # Python formatting
        if (self.project_dir / "pyproject.toml").exists():
            content = self._read_file("pyproject.toml")
            if "[tool.black]" in content:
                conventions["python_formatting"] = "Black"

        # JavaScript/TypeScript linting
        eslint_files = [
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.json",
            ".eslintrc.yml",
            "eslint.config.js",
        ]
        if any((self.project_dir / f).exists() for f in eslint_files):
            conventions["js_linting"] = "ESLint"

        # Prettier
        prettier_files = [
            ".prettierrc",
            ".prettierrc.js",
            ".prettierrc.json",
            "prettier.config.js",
        ]
        if any((self.project_dir / f).exists() for f in prettier_files):
            conventions["formatting"] = "Prettier"

        # TypeScript
        if (self.project_dir / "tsconfig.json").exists():
            conventions["typescript"] = True

        # Git hooks
        if (self.project_dir / ".husky").exists():
            conventions["git_hooks"] = "Husky"
        elif (self.project_dir / ".pre-commit-config.yaml").exists():
            conventions["git_hooks"] = "pre-commit"

        self.index["conventions"] = conventions

    def _map_dependencies(self) -> None:
        """Map dependencies between services."""
        services = self.index.get("services", {})

        for service_name, service_info in services.items():
            consumes = []

            # Check for API client patterns
            if service_info.get("type") == "frontend":
                # Frontend typically consumes backend
                for other_name, other_info in services.items():
                    if other_info.get("type") == "backend":
                        consumes.append(f"{other_name}.api")

            # Check for shared libraries
            if service_info.get("dependencies"):
                deps = service_info["dependencies"]
                for other_name in services.keys():
                    if other_name in deps or f"@{other_name}" in str(deps):
                        consumes.append(other_name)

            if consumes:
                service_info["consumes"] = consumes

    def _has_in_pyproject(self, tool: str) -> bool:
        """Check if a tool is configured in pyproject.toml."""
        if (self.project_dir / "pyproject.toml").exists():
            content = self._read_file("pyproject.toml")
            return f"[tool.{tool}]" in content
        return False

    def _read_file(self, path: str) -> str:
        try:
            return (self.project_dir / path).read_text()
        except (OSError, UnicodeDecodeError):
            return ""

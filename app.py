import click
from flask import Flask

from config import Config
from extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    import models  # noqa: F401  (register models with SQLAlchemy)

    from blueprints.dashboard import bp as dashboard_bp
    from blueprints.jobs import bp as jobs_bp
    from blueprints.companies import bp as companies_bp
    from blueprints.contacts import bp as contacts_bp
    from blueprints.interviews import bp as interviews_bp
    from blueprints.conversations import bp as conversations_bp
    from blueprints.tags import bp as tags_bp
    from blueprints.calendar import bp as calendar_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(interviews_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(calendar_bp)

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("seed")
    def seed_cmd():
        """Populate the database with sample data."""
        from seed import run

        run()
        click.echo("Sample data seeded.")

    @app.template_filter("fmt_date")
    def fmt_date(value, fmt="%Y-%m-%d"):
        if value is None:
            return ""
        return value.strftime(fmt)

    @app.template_filter("fmt_datetime")
    def fmt_datetime(value, fmt="%Y-%m-%d %H:%M"):
        if value is None:
            return ""
        return value.strftime(fmt)

    @app.template_filter("money")
    def money(value):
        if value is None:
            return ""
        return f"${value:,.0f}"

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

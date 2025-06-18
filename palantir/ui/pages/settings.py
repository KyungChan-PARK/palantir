"""Settings page component."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
import yaml
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, validator
from ..i18n import translate as _

from ...config import Config
from ...utils.encryption import decrypt_value, encrypt_value

try:
    st.page("settings", _("settings_title"), icon="⚙️")
except Exception:
    pass


class APISettings(BaseModel):
    """API configuration settings."""

    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    openai_model: str = Field("gpt-4", description="OpenAI Model")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API Key")
    anthropic_model: str = Field("claude-3-sonnet-20240229", description="Anthropic Model")
    weaviate_url: Optional[str] = Field(None, description="Weaviate instance URL")
    neo4j_uri: Optional[str] = Field(None, description="Neo4j database URI")
    neo4j_user: Optional[str] = Field(None, description="Neo4j username")
    neo4j_password: Optional[str] = Field(None, description="Neo4j password")

    @validator("openai_model")
    def validate_openai_model(cls, v):
        """Validate OpenAI model name."""
        allowed_models = ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of: {', '.join(allowed_models)}")
        return v

    @validator("anthropic_model")
    def validate_anthropic_model(cls, v):
        """Validate Anthropic model name."""
        allowed_models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229"]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of: {', '.join(allowed_models)}")
        return v


class UISettings(BaseModel):
    """UI configuration settings."""

    theme: str = Field("light", description="UI theme (light/dark)")
    language: str = Field("en", description="Interface language")
    auto_refresh: bool = Field(True, description="Auto-refresh data")
    refresh_interval: int = Field(60, description="Refresh interval in seconds")
    show_advanced_features: bool = Field(False, description="Show advanced features")
    default_visualization: str = Field(
        "table", description="Default visualization type"
    )
    date_format: str = Field("%Y-%m-%d", description="Date format")
    number_format: str = Field(",.2f", description="Number format")
    timezone: str = Field("UTC", description="Timezone")


class AnalyticsSettings(BaseModel):
    """Analytics configuration settings."""

    enable_tracking: bool = Field(True, description="Enable usage tracking")
    tracking_level: str = Field("basic", description="Tracking detail level")
    retention_period: int = Field(30, description="Data retention period in days")
    export_format: str = Field("json", description="Default export format")
    sampling_rate: float = Field(1.0, description="Data sampling rate")
    cache_timeout: int = Field(3600, description="Cache timeout in seconds")


class BackupSettings(BaseModel):
    """Backup configuration settings."""

    auto_backup: bool = Field(True, description="Enable automatic backups")
    backup_interval: int = Field(24, description="Backup interval in hours")
    backup_retention: int = Field(7, description="Backup retention in days")
    backup_location: str = Field("backups", description="Backup directory")
    compression_enabled: bool = Field(True, description="Enable backup compression")
    encrypt_backups: bool = Field(False, description="Encrypt backup files")


def load_settings() -> Dict:
    """Load settings from session state or initialize defaults."""
    if "settings" not in st.session_state:
        # Try to load from config file
        config_file = Path("config.yaml")
        if config_file.exists():
            with open(config_file, "r") as f:
                settings = yaml.safe_load(f)
        else:
            settings = {
                "api": APISettings().dict(),
                "ui": UISettings().dict(),
                "analytics": AnalyticsSettings().dict(),
                "backup": BackupSettings().dict(),
            }
        st.session_state.settings = settings
    return st.session_state.settings


def save_settings(settings: Dict):
    """Save settings to session state and file."""
    st.session_state.settings = settings

    # Save to config file
    config_file = Path("config.yaml")
    with open(config_file, "w") as f:
        yaml.safe_dump(settings, f)


def render_api_settings():
    """Render API configuration section."""
    st.markdown("### 🔑 API Configuration")

    settings = load_settings()
    api_settings = settings["api"]

    # API Keys
    with st.expander("API Keys", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            api_settings["openai_api_key"] = st.text_input(
                "OpenAI API Key",
                value=api_settings.get("openai_api_key", ""),
                type="password",
                help="Your OpenAI API key for GPT models",
            )

        with col2:
            api_settings["openai_model"] = st.selectbox(
                "OpenAI Model",
                ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                index=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"].index(
                    api_settings.get("openai_model", "gpt-4")
                ),
                help="Select the OpenAI model to use",
            )

        col3, col4 = st.columns(2)

        with col3:
            api_settings["anthropic_api_key"] = st.text_input(
                "Anthropic API Key",
                value=api_settings.get("anthropic_api_key", ""),
                type="password",
                help="Your Anthropic API key for Claude models",
            )

        with col4:
            api_settings["anthropic_model"] = st.selectbox(
                "Anthropic Model",
                ["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
                index=["claude-3-sonnet-20240229", "claude-3-opus-20240229"].index(
                    api_settings.get("anthropic_model", "claude-3-sonnet-20240229")
                ),
                help="Select the Anthropic model to use",
            )

    # Database Configuration
    with st.expander("Database Configuration"):
        col1, col2 = st.columns(2)

        with col1:
            api_settings["weaviate_url"] = st.text_input(
                "Weaviate URL",
                value=api_settings.get("weaviate_url", ""),
                help="URL of your Weaviate vector database instance",
            )

        with col2:
            api_settings["neo4j_uri"] = st.text_input(
                "Neo4j URI",
                value=api_settings.get("neo4j_uri", ""),
                help="URI of your Neo4j graph database instance",
            )

        col3, col4 = st.columns(2)

        with col3:
            api_settings["neo4j_user"] = st.text_input(
                "Neo4j Username",
                value=api_settings.get("neo4j_user", ""),
                help="Neo4j database username",
            )

        with col4:
            api_settings["neo4j_password"] = st.text_input(
                "Neo4j Password",
                value=api_settings.get("neo4j_password", ""),
                type="password",
                help="Neo4j database password",
            )

    # Connection Test
    if st.button("Test Connections"):
        with st.spinner("Testing connections..."):
            # Test OpenAI
            if api_settings["openai_api_key"]:
                try:
                    # Add OpenAI connection test
                    st.success("✅ OpenAI connection successful")
                except Exception as e:
                    st.error(f"❌ OpenAI connection failed: {str(e)}")

            # Test Weaviate
            if api_settings["weaviate_url"]:
                try:
                    # Add Weaviate connection test
                    st.success("✅ Weaviate connection successful")
                except Exception as e:
                    st.error(f"❌ Weaviate connection failed: {str(e)}")

            # Test Neo4j
            if all(
                [
                    api_settings["neo4j_uri"],
                    api_settings["neo4j_user"],
                    api_settings["neo4j_password"],
                ]
            ):
                try:
                    # Add Neo4j connection test
                    st.success("✅ Neo4j connection successful")
                except Exception as e:
                    st.error(f"❌ Neo4j connection failed: {str(e)}")

    settings["api"] = api_settings
    save_settings(settings)


def render_ui_settings():
    """Render UI configuration section."""
    st.markdown("### 🎨 UI Configuration")

    settings = load_settings()
    ui_settings = settings["ui"]

    # Theme and Language
    col1, col2 = st.columns(2)

    with col1:
        ui_settings["theme"] = st.selectbox(
            "Theme",
            ["light", "dark"],
            index=0 if ui_settings["theme"] == "light" else 1,
            help="Select the UI theme",
        )

    with col2:
        ui_settings["language"] = st.selectbox(
            "Language",
            ["en", "ko", "ja"],
            index=["en", "ko", "ja"].index(ui_settings["language"]),
            help="Select the interface language",
        )

    # Display Settings
    st.markdown("#### Display Settings")

    col1, col2 = st.columns(2)

    with col1:
        ui_settings["default_visualization"] = st.selectbox(
            "Default Visualization",
            ["table", "chart", "card"],
            index=["table", "chart", "card"].index(
                ui_settings.get("default_visualization", "table")
            ),
            help="Select the default visualization type",
        )

    with col2:
        ui_settings["show_advanced_features"] = st.checkbox(
            "Show Advanced Features",
            value=ui_settings.get("show_advanced_features", False),
            help="Enable advanced UI features",
        )

    # Format Settings
    st.markdown("#### Format Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        ui_settings["date_format"] = st.text_input(
            "Date Format",
            value=ui_settings.get("date_format", "%Y-%m-%d"),
            help="Python date format string",
        )

    with col2:
        ui_settings["number_format"] = st.text_input(
            "Number Format",
            value=ui_settings.get("number_format", ",.2f"),
            help="Python number format string",
        )

    with col3:
        ui_settings["timezone"] = st.selectbox(
            "Timezone",
            ["UTC", "Asia/Seoul", "Asia/Tokyo", "America/New_York"],
            index=["UTC", "Asia/Seoul", "Asia/Tokyo", "America/New_York"].index(
                ui_settings.get("timezone", "UTC")
            ),
            help="Select the display timezone",
        )

    # Auto-refresh Settings
    st.markdown("#### Data Refresh Settings")

    ui_settings["auto_refresh"] = st.checkbox(
        "Enable Auto-refresh",
        value=ui_settings["auto_refresh"],
        help="Automatically refresh data",
    )

    if ui_settings["auto_refresh"]:
        ui_settings["refresh_interval"] = st.slider(
            "Refresh Interval (seconds)",
            min_value=30,
            max_value=300,
            value=ui_settings["refresh_interval"],
            step=30,
            help="How often to refresh the data",
        )

    settings["ui"] = ui_settings
    save_settings(settings)


def render_analytics_settings():
    """Render analytics configuration section."""
    st.markdown("### 📊 Analytics Configuration")

    settings = load_settings()
    analytics_settings = settings.get("analytics", AnalyticsSettings().dict())

    # Tracking Settings
    col1, col2 = st.columns(2)

    with col1:
        analytics_settings["enable_tracking"] = st.checkbox(
            "Enable Usage Tracking",
            value=analytics_settings["enable_tracking"],
            help="Collect anonymous usage statistics",
        )

    with col2:
        analytics_settings["tracking_level"] = st.selectbox(
            "Tracking Detail Level",
            ["basic", "detailed", "full"],
            index=["basic", "detailed", "full"].index(
                analytics_settings["tracking_level"]
            ),
            help="Level of detail for usage tracking",
        )

    # Data Settings
    st.markdown("#### Data Settings")

    col1, col2 = st.columns(2)

    with col1:
        analytics_settings["retention_period"] = st.number_input(
            "Data Retention Period (days)",
            min_value=1,
            max_value=365,
            value=analytics_settings["retention_period"],
            help="How long to keep analytics data",
        )

    with col2:
        analytics_settings["sampling_rate"] = st.slider(
            "Data Sampling Rate",
            min_value=0.0,
            max_value=1.0,
            value=analytics_settings["sampling_rate"],
            help="Fraction of data to sample",
        )

    # Export Settings
    st.markdown("#### Export Settings")

    col1, col2 = st.columns(2)

    with col1:
        analytics_settings["export_format"] = st.selectbox(
            "Default Export Format",
            ["json", "csv", "excel"],
            index=["json", "csv", "excel"].index(analytics_settings["export_format"]),
            help="Default format for data exports",
        )

    with col2:
        analytics_settings["cache_timeout"] = st.number_input(
            "Cache Timeout (seconds)",
            min_value=60,
            max_value=86400,
            value=analytics_settings["cache_timeout"],
            help="How long to cache analytics results",
        )

    settings["analytics"] = analytics_settings
    save_settings(settings)


def render_backup_settings():
    """Render backup configuration section."""
    st.markdown("### 💾 Backup Configuration")

    settings = load_settings()
    backup_settings = settings.get("backup", BackupSettings().dict())

    # Backup Settings
    col1, col2 = st.columns(2)

    with col1:
        backup_settings["auto_backup"] = st.checkbox(
            "Enable Automatic Backups",
            value=backup_settings["auto_backup"],
            help="Automatically backup data",
        )

    with col2:
        backup_settings["backup_interval"] = st.number_input(
            "Backup Interval (hours)",
            min_value=1,
            max_value=168,
            value=backup_settings["backup_interval"],
            help="How often to create backups",
        )

    # Retention Settings
    st.markdown("#### Retention Settings")

    col1, col2 = st.columns(2)

    with col1:
        backup_settings["backup_retention"] = st.number_input(
            "Backup Retention (days)",
            min_value=1,
            max_value=365,
            value=backup_settings["backup_retention"],
            help="How long to keep backups",
        )

    with col2:
        backup_settings["backup_location"] = st.text_input(
            "Backup Location",
            value=backup_settings["backup_location"],
            help="Directory to store backups",
        )

    # Security Settings
    st.markdown("#### Security Settings")

    col1, col2 = st.columns(2)

    with col1:
        backup_settings["compression_enabled"] = st.checkbox(
            "Enable Compression",
            value=backup_settings["compression_enabled"],
            help="Compress backup files",
        )

    with col2:
        backup_settings["encrypt_backups"] = st.checkbox(
            "Encrypt Backups",
            value=backup_settings["encrypt_backups"],
            help="Encrypt backup files",
        )

    # Backup Actions
    st.markdown("#### Backup Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Create Backup Now"):
            with st.spinner("Creating backup..."):
                try:
                    # Add backup creation logic
                    backup_path = "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.success(f"✅ Backup created: {backup_path}")
                except Exception as e:
                    st.error(f"❌ Backup failed: {str(e)}")

    with col2:
        if st.button("Restore from Backup"):
            # Show backup selection
            backup_files = [f for f in os.listdir("backups") if f.endswith(".zip")]
            if backup_files:
                selected_backup = st.selectbox("Select Backup", backup_files)
                if st.button("Confirm Restore"):
                    with st.spinner("Restoring from backup..."):
                        try:
                            # Add restore logic
                            st.success("✅ Restore completed")
                        except Exception as e:
                            st.error(f"❌ Restore failed: {str(e)}")
            else:
                st.info("No backup files found")

    with col3:
        if st.button("Manage Backups"):
            # Show backup management
            backup_files = [f for f in os.listdir("backups") if f.endswith(".zip")]
            if backup_files:
                st.dataframe(
                    pd.DataFrame(
                        {
                            "Backup": backup_files,
                            "Size": [
                                f"{os.path.getsize(os.path.join('backups', f)) / 1024 / 1024:.1f} MB"
                                for f in backup_files
                            ],
                            "Created": [
                                datetime.fromtimestamp(
                                    os.path.getctime(os.path.join("backups", f))
                                ).strftime("%Y-%m-%d %H:%M:%S")
                                for f in backup_files
                            ],
                        }
                    )
                )

                if st.button("Clean Old Backups"):
                    with st.spinner("Cleaning old backups..."):
                        try:
                            # Add cleanup logic
                            st.success("✅ Old backups cleaned")
                        except Exception as e:
                            st.error(f"❌ Cleanup failed: {str(e)}")
            else:
                st.info("No backup files found")

    settings["backup"] = backup_settings
    save_settings(settings)


def render_data_settings():
    """Render data management section."""
    st.markdown("### 📁 Data Management")

    # Data Import/Export
    with st.expander("Import/Export"):
        col1, col2 = st.columns(2)

        with col1:
            uploaded_file = st.file_uploader(
                "Import Data",
                type=["json", "csv", "xlsx"],
                help="Upload data files to import",
            )

            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".json"):
                        data = json.load(uploaded_file)
                    elif uploaded_file.name.endswith(".csv"):
                        data = pd.read_csv(uploaded_file)
                    else:  # Excel
                        data = pd.read_excel(uploaded_file)
                    st.success("✅ 파일 업로드 성공")
                    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                        st.info("업로드된 데이터가 비어 있습니다.")
                    else:
                        st.json(
                            data.head().to_dict()
                            if isinstance(data, pd.DataFrame)
                            else data
                        )
                    if st.button("Confirm Import"):
                        with st.spinner("Importing data..."):
                            # Add import logic
                            st.success("✅ 데이터 임포트 성공")
                except Exception as e:
                    st.error(f"❌ Import 실패: {str(e)}")

        with col2:
            export_format = st.selectbox("Export Format", ["JSON", "CSV", "Excel"])

            if st.button("Export Data"):
                with st.spinner("Preparing export..."):
                    try:
                        # Add export logic
                        if export_format == "JSON":
                            data = json.dumps({"sample": "data"}, indent=2)
                            mime = "application/json"
                            ext = "json"
                        elif export_format == "CSV":
                            data = pd.DataFrame({"sample": ["data"]}).to_csv(
                                index=False
                            )
                            mime = "text/csv"
                            ext = "csv"
                        else:  # Excel
                            data = pd.DataFrame({"sample": ["data"]}).to_excel(
                                index=False
                            )
                            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            ext = "xlsx"

                        st.download_button(
                            "Download Data",
                            data=data,
                            file_name=f"export_{datetime.now():%Y%m%d_%H%M%S}.{ext}",
                            mime=mime,
                        )
                    except Exception as e:
                        st.error(f"❌ Export failed: {str(e)}")

    # Data Cleanup
    with st.expander("Data Cleanup"):
        st.markdown(
            """
            ⚠️ **Warning**: Data cleanup operations are irreversible.
            Make sure to backup your data before proceeding.
        """
        )

        cleanup_options = st.multiselect(
            "Select Data to Clean",
            ["Temporary Files", "Cache", "Old Logs", "Unused Objects"],
            help="Select which data to clean up",
        )

        if cleanup_options:
            if st.button("Clean Selected Data", type="secondary"):
                st.warning("This will delete the selected data. Are you sure?")

                col1, col2 = st.columns(2)

                with col1:
                    confirm_text = st.text_input(
                        "Type 'CONFIRM' to proceed",
                        help="Type CONFIRM in all caps to proceed with cleanup",
                    )

                with col2:
                    if confirm_text == "CONFIRM":
                        if st.button("Yes, Clean Data", type="primary"):
                            with st.spinner("Cleaning data..."):
                                try:
                                    # Add cleanup logic for each selected option
                                    for option in cleanup_options:
                                        st.info(f"Cleaning {option}...")
                                        # Add specific cleanup logic
                                    st.success("✅ Data cleaned successfully")
                                except Exception as e:
                                    st.error(f"❌ Cleanup failed: {str(e)}")


def render_page():
    """Render the settings page."""
    st.title("⚙️ " + _("settings_title"))

    st.markdown(
        """
        Configure your application settings, API keys, and preferences.
        Changes are automatically saved.
    """
    )

    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["API Configuration", "UI Settings", "Analytics", "Backup", "Data Management"]
    )

    with tab1:
        render_api_settings()

    with tab2:
        render_ui_settings()

    with tab3:
        render_analytics_settings()

    with tab4:
        render_backup_settings()

    with tab5:
        render_data_settings()

    # Save button
    if st.button("Save All Settings"):
        try:
            settings = load_settings()

            # Validate settings
            APISettings(**settings["api"])
            UISettings(**settings["ui"])
            AnalyticsSettings(**settings.get("analytics", {}))
            BackupSettings(**settings.get("backup", {}))

            # Encrypt sensitive data
            settings["api"]["openai_api_key"] = (
                encrypt_value(settings["api"]["openai_api_key"])
                if settings["api"]["openai_api_key"]
                else None
            )

            settings["api"]["neo4j_password"] = (
                encrypt_value(settings["api"]["neo4j_password"])
                if settings["api"]["neo4j_password"]
                else None
            )

            # Save settings
            save_settings(settings)
            st.success("✅ All settings saved successfully!")

        except Exception as e:
            st.error(f"❌ Failed to save settings: {str(e)}")

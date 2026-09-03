from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import gspread  #type: ignore
from google.oauth2.service_account import Credentials   #type: ignore
from gspread_dataframe import get_as_dataframe, set_with_dataframe  #type: ignore


@dataclass(slots=True)
class GoogleSheetsConfig:
    """Configuration for connecting to a Google Sheet."""

    credentials_path: str | Path | None = None
    scopes: tuple[str, ...] = (
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    )

    @property
    def resolved_credentials_path(self) -> Path | None:
        if self.credentials_path is None:
            env_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if env_path:
                return Path(env_path)
            return None
        return Path(self.credentials_path)


class GoogleSheetsConnector:
    """Thin wrapper around gspread for project-specific reads and writes."""

    def __init__(
        self,
        credentials_path: str | Path | None = None,
        scopes: tuple[str, ...] | None = None,
    ) -> None:
        self.config = GoogleSheetsConfig(
            credentials_path=credentials_path,
            scopes=scopes
            or (
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ),
        )

    def _get_credentials(self) -> Credentials:
        credentials_path = self.config.resolved_credentials_path
        if credentials_path is None or not credentials_path.exists():
            raise FileNotFoundError(
                "Google service account JSON not found. Set GOOGLE_SERVICE_ACCOUNT_JSON or pass credentials_path."
            )

        return Credentials.from_service_account_file(
            str(credentials_path),
            scopes=list(self.config.scopes),
        )

    def get_client(self) -> gspread.Client:
        return gspread.authorize(self._get_credentials())

    def get_worksheet(
        self,
        spreadsheet_id: str,
        worksheet_name: str | None = None,
        gid: int | None = None,
    ):
        client = self.get_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        if worksheet_name:
            return spreadsheet.worksheet(worksheet_name)
        if gid is not None:
            return spreadsheet.get_worksheet_by_id(gid)
        raise ValueError("Either worksheet_name or gid must be provided.")

    def read_dataframe(
        self,
        spreadsheet_id: str,
        worksheet_name: str | None = None,
        gid: int | None = None,
        **read_kwargs: Any,
    ) -> pd.DataFrame:
        worksheet = self.get_worksheet(
            spreadsheet_id, worksheet_name=worksheet_name, gid=gid
        )
        return get_as_dataframe(worksheet, **read_kwargs)

    def write_dataframe(
        self,
        df: pd.DataFrame,
        spreadsheet_id: str,
        worksheet_name: str,
        clear_existing: bool = True,
        **to_excel_kwargs: Any,
    ) -> None:
        client = self.get_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, rows="1000", cols="26"
            )

        if clear_existing:
            worksheet.clear()

        set_with_dataframe(
            worksheet, df, include_index=False, resize=True, **to_excel_kwargs
        )


__all__ = ["GoogleSheetsConfig", "GoogleSheetsConnector"]

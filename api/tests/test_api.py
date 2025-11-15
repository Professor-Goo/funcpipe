"""
Integration tests for API endpoints.

Tests the complete API workflow from file upload to pipeline execution.
NO MOCK DATA - Real end-to-end testing.
"""

import io

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "checks" in data


class TestFileUpload:
    """Tests for file upload endpoints."""

    def test_upload_csv_file(self, client, sample_csv_data):
        """Test uploading a valid CSV file."""
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        response = client.post("/api/files/upload", files=files)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["filename"] == "test.csv"
        assert data["format"] == "csv"
        assert data["size"] > 0
        assert data["record_count"] == 4
        assert "id" in data

    def test_upload_json_file(self, client, sample_json_data):
        """Test uploading a valid JSON file."""
        files = {"file": ("test.json", io.BytesIO(sample_json_data), "application/json")}
        response = client.post("/api/files/upload", files=files)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["filename"] == "test.json"
        assert data["format"] == "json"
        assert data["record_count"] == 4

    def test_upload_invalid_extension(self, client):
        """Test uploading file with invalid extension."""
        invalid_data = b"test data"
        files = {"file": ("test.exe", io.BytesIO(invalid_data), "application/octet-stream")}
        response = client.post("/api/files/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_empty_file(self, client):
        """Test uploading empty file."""
        files = {"file": ("test.csv", io.BytesIO(b""), "text/csv")}
        response = client.post("/api/files/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestFileManagement:
    """Tests for file management endpoints."""

    def test_list_files(self, client, sample_csv_data):
        """Test listing uploaded files."""
        # Upload a file first
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        upload_response = client.post("/api/files/upload", files=files)
        assert upload_response.status_code == status.HTTP_201_CREATED

        # List files
        response = client.get("/api/files")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "files" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_file_info(self, client, sample_csv_data):
        """Test getting file information."""
        # Upload file
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["id"]

        # Get file info
        response = client.get(f"/api/files/{file_id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == file_id
        assert data["filename"] == "test.csv"

    def test_get_nonexistent_file(self, client):
        """Test getting info for non-existent file."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/files/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_preview_file(self, client, sample_csv_data):
        """Test previewing file data."""
        # Upload file
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["id"]

        # Preview file
        response = client.get(f"/api/files/{file_id}/preview?limit=2")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 4
        assert data["data"][0]["name"] == "Alice"

    def test_delete_file(self, client, sample_csv_data):
        """Test deleting file."""
        # Upload file
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["id"]

        # Delete file
        response = client.delete(f"/api/files/{file_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify file is gone
        get_response = client.get(f"/api/files/{file_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestPipelineExecution:
    """Tests for pipeline execution."""

    def test_execute_simple_pipeline(self, client, sample_csv_data):
        """Test executing a simple pipeline."""
        # Upload file
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["id"]

        # Execute pipeline
        pipeline_request = {
            "file_id": file_id,
            "operations": [
                {
                    "type": "filter",
                    "operation": "greater_than",
                    "config": {"field": "age", "value": 27}
                }
            ],
            "preview": False
        }

        response = client.post("/api/pipelines/execute", json=pipeline_request)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "completed"
        assert "data" in data
        assert data["record_count"] == 3  # Alice, Charlie, Diana
        assert "execution_time_ms" in data

    def test_execute_complex_pipeline(self, client, sample_csv_data):
        """Test executing pipeline with multiple operations."""
        # Upload file
        files = {"file": ("test.csv", io.BytesIO(sample_csv_data), "text/csv")}
        upload_response = client.post("/api/files/upload", files=files)
        file_id = upload_response.json()["id"]

        # Execute complex pipeline
        pipeline_request = {
            "file_id": file_id,
            "operations": [
                {
                    "type": "filter",
                    "operation": "greater_than",
                    "config": {"field": "age", "value": 25}
                },
                {
                    "type": "transform",
                    "operation": "multiply_field",
                    "config": {"field": "salary", "factor": 1.1}
                },
                {
                    "type": "sort",
                    "operation": "sort",
                    "config": {"field": "salary", "reverse": True}
                },
                {
                    "type": "take",
                    "operation": "take",
                    "config": {"n": 2}
                }
            ],
            "preview": False
        }

        response = client.post("/api/pipelines/execute", json=pipeline_request)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "completed"
        assert data["record_count"] == 2
        # Verify salary was multiplied
        assert data["data"][0]["salary"] > 50000

    def test_validate_pipeline(self, client):
        """Test pipeline validation."""
        validation_request = {
            "operations": [
                {
                    "type": "filter",
                    "operation": "greater_than",
                    "config": {"field": "age", "value": 25}
                }
            ]
        }

        response = client.post("/api/pipelines/validate", json=validation_request)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["valid"] is True
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)

    def test_validate_invalid_pipeline(self, client):
        """Test validation of invalid pipeline."""
        validation_request = {
            "operations": [
                {
                    "type": "filter",
                    "operation": "nonexistent_operation",
                    "config": {}
                }
            ]
        }

        response = client.post("/api/pipelines/validate", json=validation_request)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestSavedPipelines:
    """Tests for saved pipeline management."""

    def test_save_pipeline(self, client):
        """Test saving a pipeline."""
        save_request = {
            "name": "Test Pipeline",
            "description": "A test pipeline",
            "operations": [
                {
                    "type": "filter",
                    "operation": "greater_than",
                    "config": {"field": "age", "value": 25}
                }
            ],
            "tags": ["test", "demo"]
        }

        response = client.post("/api/pipelines", json=save_request)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == "Test Pipeline"
        assert data["description"] == "A test pipeline"
        assert len(data["tags"]) == 2
        assert "id" in data

    def test_list_saved_pipelines(self, client):
        """Test listing saved pipelines."""
        # Save a pipeline first
        save_request = {
            "name": "Test Pipeline",
            "operations": [
                {
                    "type": "filter",
                    "operation": "equals",
                    "config": {"field": "status", "value": "active"}
                }
            ]
        }
        save_response = client.post("/api/pipelines", json=save_request)
        assert save_response.status_code == status.HTTP_201_CREATED

        # List pipelines
        response = client.get("/api/pipelines")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "pipelines" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_saved_pipeline(self, client):
        """Test getting saved pipeline."""
        # Save pipeline
        save_request = {
            "name": "Test Pipeline",
            "operations": [
                {
                    "type": "transform",
                    "operation": "upper_field",
                    "config": {"field": "name"}
                }
            ]
        }
        save_response = client.post("/api/pipelines", json=save_request)
        pipeline_id = save_response.json()["id"]

        # Get pipeline
        response = client.get(f"/api/pipelines/{pipeline_id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == pipeline_id
        assert data["name"] == "Test Pipeline"

    def test_delete_saved_pipeline(self, client):
        """Test deleting saved pipeline."""
        # Save pipeline
        save_request = {
            "name": "Test Pipeline",
            "operations": [
                {
                    "type": "filter",
                    "operation": "is_not_null",
                    "config": {"field": "email"}
                }
            ]
        }
        save_response = client.post("/api/pipelines", json=save_request)
        pipeline_id = save_response.json()["id"]

        # Delete pipeline
        response = client.delete(f"/api/pipelines/{pipeline_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        get_response = client.get(f"/api/pipelines/{pipeline_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestOperations:
    """Tests for operations metadata endpoints."""

    def test_list_operations(self, client):
        """Test listing all operations."""
        response = client.get("/api/operations")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "filters" in data
        assert "transforms" in data
        assert "utilities" in data

        # Verify we have operations
        assert len(data["filters"]) > 0
        assert len(data["transforms"]) > 0
        assert len(data["utilities"]) > 0

    def test_get_specific_operation(self, client):
        """Test getting specific operation details."""
        response = client.get("/api/operations/greater_than")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["name"] == "greater_than"
        assert data["type"] == "filter"
        assert "parameters" in data
        assert "examples" in data

    def test_get_nonexistent_operation(self, client):
        """Test getting non-existent operation."""
        response = client.get("/api/operations/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

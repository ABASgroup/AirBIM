from pydantic import BaseModel, model_validator


class FileUploadRequest(BaseModel):
    filename: str
    size: int

    @model_validator(mode='after')
    def format_extension(self):
        "Adds point in extension."
        if self.extension[0] != ".":
            self.extension = "." + self.extension
        return self


class FileLinkPublic(BaseModel):
    """API Response schema"""
    project_id: int
    presigned_url: str
    filename: str
    extension: str
    size: int

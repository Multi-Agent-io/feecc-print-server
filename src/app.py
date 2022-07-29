import typing as tp

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from auth.dependencies import authenticate
from feecc_printer.Printer import Printer
from feecc_printer.models import GenericResponse
from logging_config import CONSOLE_LOGGING_CONFIG, FILE_LOGGING_CONFIG

# apply logging configuration
logger.configure(handlers=[CONSOLE_LOGGING_CONFIG, FILE_LOGGING_CONFIG])

# set up an ASGI app
app = FastAPI(
    title="Feecc Print server",
    description="A printing server for Feecc QA system",
    dependencies=[Depends(authenticate)],
)

# allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate printer
PRINTER = Printer()


@app.post("/print_image", response_model=GenericResponse)
def print_image(image_file: bytes = File(...), annotation: tp.Optional[str] = Form(None)) -> GenericResponse:
    """Print an image using label printer and annotate if necessary"""
    try:
        PRINTER.print_image(image_file, annotation)
        message = "Task handled as expected"
        logger.info(message)
        return GenericResponse(status=status.HTTP_200_OK, details=message)

    except Exception as e:
        message = f"An error occurred while printing the image: {e}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message) from e


if __name__ == "__main__":
    uvicorn.run("app:app", port=8083)

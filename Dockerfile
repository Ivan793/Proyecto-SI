FROM public.ecr.aws/lambda/python:3.12

# Set working directory
# Copy requirements first for better layer caching
COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY firebase_credentials.json ${LAMBDA_TASK_ROOT}


# Install dependencies
RUN pip3 install -r requirements.txt

COPY ./app ${LAMBDA_TASK_ROOT}/app


# Run the application using uvicorn (since you have FastAPI)
CMD ["app.main.handler"]
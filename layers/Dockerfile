FROM public.ecr.aws/lambda/python:3.12

# Set environment variables
ENV LAMBDA_TASK_ROOT=/var/task
ENV PYTHONPATH=$LAMBDA_TASK_ROOT

COPY install.sh /root

ENTRYPOINT ["/bin/sh"]

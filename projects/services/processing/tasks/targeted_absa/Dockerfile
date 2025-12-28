FROM airflow-base:2.9.0-custom
USER airflow
# Copy file requirements riêng của module này
COPY projects/services/processing/tasks/targeted_absa/requirements.txt /tmp/absa_requirements.txt
# Cài đặt thư viện (no-cache để giảm dung lượng image)
RUN pip install --no-cache-dir -r /tmp/absa_requirements.txt

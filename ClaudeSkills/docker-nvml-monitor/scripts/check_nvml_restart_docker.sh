#!/bin/bash
LOG_FILE=/var/log/nvml_check.log
CONTAINERS=("CONTAINER_PLACEHOLDER")
MAX_WAIT_MINUTES=60  # 最多等待60分钟

for CONTAINER_NAME in "${CONTAINERS[@]}"; do
    echo "[$(date)] Checking NVML status for container: $CONTAINER_NAME" >> $LOG_FILE
    
    # 使用 docker exec 在容器内执行 nvidia-smi
    NVML_CHECK=$(docker exec $CONTAINER_NAME nvidia-smi 2>&1)
    
    if echo "$NVML_CHECK" | grep -qi "NVML.*ERROR\|Failed to initialize NVML"; then
        echo "[$(date)] NVML ERROR detected in $CONTAINER_NAME" >> $LOG_FILE
        echo "[$(date)] Waiting for GPU processes to complete..." >> $LOG_FILE
        
        # 等待 GPU 进程完成
        WAIT_COUNT=0
        while [ $WAIT_COUNT -lt $MAX_WAIT_MINUTES ]; do
            GPU_PROCESSES=$(docker exec $CONTAINER_NAME nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
            
            if [ "$GPU_PROCESSES" -eq 0 ]; then
                echo "[$(date)] All GPU processes completed, restarting container $CONTAINER_NAME..." >> $LOG_FILE
                docker restart $CONTAINER_NAME
                echo "[$(date)] Container $CONTAINER_NAME restarted" >> $LOG_FILE
                break
            fi
            
            echo "[$(date)] Still $GPU_PROCESSES GPU processes running, waiting... ($WAIT_COUNT/$MAX_WAIT_MINUTES min)" >> $LOG_FILE
            sleep 60
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        
        if [ $WAIT_COUNT -eq $MAX_WAIT_MINUTES ]; then
            echo "[$(date)] Timeout waiting for GPU processes, skipping restart for $CONTAINER_NAME" >> $LOG_FILE
        fi
    else
        echo "[$(date)] NVML check passed for $CONTAINER_NAME" >> $LOG_FILE
    fi
done

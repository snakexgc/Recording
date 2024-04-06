#!/bin/bash
TARGETS=("www.google.com" "www.baidu.com" "www.huawei.com")
RECOVERY_SCRIPT="/path/to/recovery/script.sh"
check_network() {
    for target in "${TARGETS[@]}"; do
        if ping -c 1 -W 5 "$target" &> /dev/null; then
            echo "$(date): $target is up"
            return 0
        else
            echo "$(date): $target is down"
        fi
    done
    return 1
}
if check_network; then
    echo "Network is up"
else
    echo "Network is down, executing recovery script..."
    $RECOVERY_SCRIPT
fi

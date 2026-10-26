#!/usr/bin/env bash
# Run on the Pi after copying reviewed source to /opt/hnsg.
# No formatting, deletion, database migration or replacement of existing services.
set -euo pipefail
cd /opt/hnsg
mountpoint -q /mnt/innotech-usb
test ! -e /etc/systemd/system/hnsg-demo.service || { echo 'Servico existente: revisar atualizacao manualmente'; exit 2; }
test ! -e /etc/hnsg/demo.env || { echo 'Ambiente existente: preservar e revisar manualmente'; exit 2; }
if ! id hnsg >/dev/null 2>&1; then
    sudo -n useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin hnsg
fi
sudo -n install -d -o root -g root -m 755 /mnt/innotech-usb/hnsg
sudo -n install -d -o hnsg -g hnsg -m 700 /mnt/innotech-usb/hnsg/runtime
sudo -n install -d -o innotech -g innotech -m 700 /mnt/innotech-usb/hnsg/build
sudo -n install -d -o innotech -g innotech -m 755 /mnt/innotech-usb/hnsg/venv
python3 -m venv /mnt/innotech-usb/hnsg/venv
TMPDIR=/mnt/innotech-usb/hnsg/build /mnt/innotech-usb/hnsg/venv/bin/python -m pip install --no-cache-dir -r requirements.txt
sudo -n chown -R root:root /mnt/innotech-usb/hnsg/venv
sudo -n chmod -R a+rX /mnt/innotech-usb/hnsg/venv
sudo -n install -d -o root -g hnsg -m 750 /etc/hnsg
sudo -n install -o root -g hnsg -m 640 deploy/hnsg-demo.env.example /etc/hnsg/demo.env
sudo -n install -o root -g root -m 644 deploy/hnsg-demo.service /etc/systemd/system/hnsg-demo.service
sudo -n systemd-analyze verify /etc/systemd/system/hnsg-demo.service
sudo -n systemctl daemon-reload
echo 'Instalado. Crie o administrador antes de habilitar hnsg-demo.service.'
echo 'Funnel (publicacao explicita): sudo tailscale funnel --bg --https=8443 --yes http://127.0.0.1:8016'

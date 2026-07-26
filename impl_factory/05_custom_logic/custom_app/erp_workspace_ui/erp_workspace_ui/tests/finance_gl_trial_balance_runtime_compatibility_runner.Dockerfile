# syntax=docker/dockerfile:1.7

# BASE_IMAGE has deliberately no default.  The later materialization gate must
# supply one deployment-equivalent lowercase repository@sha256 reference.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

USER 0:0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/erpai

COPY --chown=1000:1000 --chmod=0555 \
    finance_gl_trial_balance_runtime_compatibility_probe.py \
    /opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py
COPY --chown=1000:1000 --chmod=0555 \
    finance_gl_trial_balance_runtime_compatibility_site_initializer.py \
    /opt/erpai/finance_gl_trial_balance_runtime_compatibility_site_initializer.py

# The immutable base must expose the resolved stack interpreter at this exact
# path. Its artifact manifest must prove a concrete >=3.14,<3.15 build. The
# empty sites directory is copied into a fresh named volume so its root remains
# owned and writable only by the fixed runner identity.
RUN ["/usr/bin/python3.14", "-I", "-c", "import os,shutil,sys; from pathlib import Path; assert (3,14) <= sys.version_info[:2] < (3,15); p=Path('/home/frappe/frappe-bench/sites'); p.mkdir(parents=True,exist_ok=True); [(q.unlink() if q.is_symlink() or q.is_file() else shutil.rmtree(q)) for q in tuple(p.iterdir())]; os.chown(p,1000,1000); os.chmod(p,0o700)"]

USER 1000:1000

ENTRYPOINT ["/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py"]

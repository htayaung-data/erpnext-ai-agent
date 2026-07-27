# The built-in frontend of the separately pinned Engine/BuildKit is mandatory.
# No external Dockerfile frontend image is selected by this source package.
FROM docker.io/frappe/erpnext@sha256:63e3db0e981a6e34e250635fa6f1d52cb96e10f66e6f34393c80b6fe4329c2d0

ARG SOURCE_REPOSITORY_REVISION
ARG FRAPPE_REVISION
ARG ERPNEXT_REVISION
ARG BUILD_CONTEXT_MANIFEST_SHA256
ARG BUILD_MANIFEST_SHA256
ARG SOURCE_CONTENT_SHA256
ARG FRAPPE_TREE_SHA256
ARG ERPNEXT_TREE_SHA256
ARG PACKAGE_INITIALIZER_SHA256
ARG FINANCE_INITIALIZER_SHA256
ARG CORE_SHA256
ARG ADAPTER_SHA256
ARG RUNTIME_SHA256
ARG PROBE_SHA256
ARG INITIALIZER_SHA256
ARG RUNNER_PYTHON_VERSION
ARG RUNNER_PYTHON_SHA256
ARG DOCKERFILE_SHA256

USER 0:0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/home/frappe/frappe-bench/apps/frappe:/home/frappe/frappe-bench/apps/erpnext:/home/frappe/frappe-bench/apps/erp_workspace_ui \
    ERPAI_FRONTEND_POLICY=engine_builtin \
    ERPAI_SOURCE_REPOSITORY_REVISION=${SOURCE_REPOSITORY_REVISION} \
    ERPAI_FRAPPE_REVISION=${FRAPPE_REVISION} \
    ERPAI_ERPNEXT_REVISION=${ERPNEXT_REVISION} \
    ERPAI_BUILD_CONTEXT_MANIFEST_SHA256=${BUILD_CONTEXT_MANIFEST_SHA256} \
    ERPAI_BUILD_MANIFEST_SHA256=${BUILD_MANIFEST_SHA256} \
    ERPAI_SOURCE_CONTENT_SHA256=${SOURCE_CONTENT_SHA256} \
    ERPAI_DOCKERFILE_SHA256=${DOCKERFILE_SHA256} \
    ERPAI_FRAPPE_TREE_SHA256=${FRAPPE_TREE_SHA256} \
    ERPAI_ERPNEXT_TREE_SHA256=${ERPNEXT_TREE_SHA256} \
    ERPAI_PACKAGE_INITIALIZER_SHA256=${PACKAGE_INITIALIZER_SHA256} \
    ERPAI_FINANCE_INITIALIZER_SHA256=${FINANCE_INITIALIZER_SHA256} \
    ERPAI_CORE_SHA256=${CORE_SHA256} \
    ERPAI_ADAPTER_SHA256=${ADAPTER_SHA256} \
    ERPAI_RUNTIME_SHA256=${RUNTIME_SHA256} \
    ERPAI_PROBE_SHA256=${PROBE_SHA256} \
    ERPAI_INITIALIZER_SHA256=${INITIALIZER_SHA256} \
    ERPAI_RUNNER_PYTHON_VERSION=${RUNNER_PYTHON_VERSION} \
    ERPAI_RUNNER_PYTHON_SHA256=${RUNNER_PYTHON_SHA256}

WORKDIR /opt/erpai

# Remove every inherited product tree before any pinned replacement is copied.
RUN ["/usr/local/bin/python3.14", "-I", "-c", "import hashlib,os,platform,re,shutil,sys; from pathlib import Path; assert sys.executable == '/usr/local/bin/python3.14'; assert sys.version_info[:2] == (3,14); expected={'ERPAI_FRAPPE_REVISION':'4dfcc56090eb3101d18ddb03750391511f163fcf','ERPAI_ERPNEXT_REVISION':'d74a649016d8bb12ee3c5a24361171cebe860bfc','ERPAI_FRONTEND_POLICY':'engine_builtin'}; assert all(os.environ.get(k)==v for k,v in expected.items()); assert re.fullmatch(r'[0-9a-f]{40}',os.environ.get('ERPAI_SOURCE_REPOSITORY_REVISION','')); hash_keys=('ERPAI_BUILD_CONTEXT_MANIFEST_SHA256','ERPAI_BUILD_MANIFEST_SHA256','ERPAI_SOURCE_CONTENT_SHA256','ERPAI_DOCKERFILE_SHA256','ERPAI_FRAPPE_TREE_SHA256','ERPAI_ERPNEXT_TREE_SHA256','ERPAI_PACKAGE_INITIALIZER_SHA256','ERPAI_FINANCE_INITIALIZER_SHA256','ERPAI_CORE_SHA256','ERPAI_ADAPTER_SHA256','ERPAI_RUNTIME_SHA256','ERPAI_PROBE_SHA256','ERPAI_INITIALIZER_SHA256','ERPAI_RUNNER_PYTHON_SHA256'); assert all(re.fullmatch(r'[0-9a-f]{64}',os.environ.get(k,'')) for k in hash_keys); assert platform.python_version()==os.environ['ERPAI_RUNNER_PYTHON_VERSION']; assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()==os.environ['ERPAI_RUNNER_PYTHON_SHA256']; apps=Path('/home/frappe/frappe-bench/apps'); assert apps.is_dir() and not apps.is_symlink(); [(p.unlink() if p.is_symlink() or p.is_file() else shutil.rmtree(p)) for p in tuple(apps.iterdir())]; opt=Path('/opt/erpai'); [(p.unlink() if p.is_symlink() or p.is_file() else shutil.rmtree(p)) for p in tuple(opt.iterdir())]"]

COPY --chown=1000:1000 --chmod=0555 frappe/ /home/frappe/frappe-bench/apps/frappe/
COPY --chown=1000:1000 --chmod=0555 erpnext/ /home/frappe/frappe-bench/apps/erpnext/
COPY --chown=1000:1000 --chmod=0444 erp_workspace_ui/erp_workspace_ui/__init__.py /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/__init__.py
COPY --chown=1000:1000 --chmod=0444 erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py
COPY --chown=1000:1000 --chmod=0444 erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py
COPY --chown=1000:1000 --chmod=0444 erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py
COPY --chown=1000:1000 --chmod=0444 erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py /home/frappe/frappe-bench/apps/erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py
COPY --chown=1000:1000 --chmod=0555 finance_gl_trial_balance_runtime_compatibility_probe.py /opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py
COPY --chown=1000:1000 --chmod=0555 finance_gl_trial_balance_runtime_compatibility_site_initializer.py /opt/erpai/finance_gl_trial_balance_runtime_compatibility_site_initializer.py
COPY --chown=1000:1000 --chmod=0444 runner-content-build-manifest.json /opt/erpai/runner-content-build-manifest.json

# Normalize copied roots, reject links/special files, and prepare only the disposable sites directory.
RUN ["/usr/local/bin/python3.14", "-I", "-c", "import hashlib,json,os,shutil,sys; from pathlib import Path; assert sys.executable == '/usr/local/bin/python3.14'; manifest_path=Path('/opt/erpai/runner-content-build-manifest.json'); raw=manifest_path.read_bytes(); assert hashlib.sha256(raw).hexdigest()==os.environ['ERPAI_BUILD_MANIFEST_SHA256']; doc=json.loads(raw.decode('utf-8','strict')); assert set(doc)=={'schema','source_repository_revision','frappe_revision','erpnext_revision','entries','entries_sha256'}; assert doc['schema']=='erpai.gl_tb.runtime_compat.build_context.v1'; assert doc['source_repository_revision']==os.environ['ERPAI_SOURCE_REPOSITORY_REVISION']; assert doc['frappe_revision']==os.environ['ERPAI_FRAPPE_REVISION']; assert doc['erpnext_revision']==os.environ['ERPAI_ERPNEXT_REVISION']; canonical=(json.dumps(doc['entries'],allow_nan=False,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n').encode(); assert hashlib.sha256(canonical).hexdigest()==doc['entries_sha256']; by_path={entry['path']:entry for entry in doc['entries']}; expected_hashes={'frappe':'ERPAI_FRAPPE_TREE_SHA256','erpnext':'ERPAI_ERPNEXT_TREE_SHA256','erp_workspace_ui/erp_workspace_ui/__init__.py':'ERPAI_PACKAGE_INITIALIZER_SHA256','erp_workspace_ui/erp_workspace_ui/finance_accounting/__init__.py':'ERPAI_FINANCE_INITIALIZER_SHA256','erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_core.py':'ERPAI_CORE_SHA256','erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_adapter.py':'ERPAI_ADAPTER_SHA256','erp_workspace_ui/erp_workspace_ui/finance_accounting/gl_trial_balance_frappe_runtime.py':'ERPAI_RUNTIME_SHA256','finance_gl_trial_balance_runtime_compatibility_probe.py':'ERPAI_PROBE_SHA256','finance_gl_trial_balance_runtime_compatibility_site_initializer.py':'ERPAI_INITIALIZER_SHA256'}; assert set(by_path)==set(expected_hashes); assert all(by_path[p]['sha256']==os.environ[k] for p,k in expected_hashes.items()); apps=Path('/home/frappe/frappe-bench/apps'); roots=(apps/'frappe',apps/'erpnext',apps/'erp_workspace_ui'); os.chown(apps,1000,1000); os.chmod(apps,0o555); scripts={Path('/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py'),Path('/opt/erpai/finance_gl_trial_balance_runtime_compatibility_site_initializer.py')}; files=scripts|{manifest_path}; assert all(not p.is_symlink() and (p.is_dir() or p.is_file()) for root in roots for p in (root,*root.rglob('*'))); [(os.chown(p,1000,1000),os.chmod(p,0o555 if p.is_dir() else 0o444)) for root in roots for p in (root,*root.rglob('*'))]; [(os.chown(p,1000,1000),os.chmod(p,0o555 if p in scripts else 0o444)) for p in files]; opt=Path('/opt/erpai'); os.chown(opt,1000,1000); os.chmod(opt,0o555); sites=Path('/home/frappe/frappe-bench/sites'); sites.mkdir(parents=True,exist_ok=True); assert not sites.is_symlink(); [(p.unlink() if p.is_symlink() or p.is_file() else shutil.rmtree(p)) for p in tuple(sites.iterdir())]; os.chown(sites,1000,1000); os.chmod(sites,0o700)"]

USER 1000:1000

ENTRYPOINT ["/opt/erpai/finance_gl_trial_balance_runtime_compatibility_probe.py"]
CMD []

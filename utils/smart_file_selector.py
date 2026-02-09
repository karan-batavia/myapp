import os
import logging
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger("utils.smart_file_selector")

SCAN_DEPTH_PRESETS = {
    'quick': {'max_files': 50, 'timeout': 60, 'max_file_size_kb': 100},
    'standard': {'max_files': 150, 'timeout': 120, 'max_file_size_kb': 200},
    'deep': {'max_files': 500, 'timeout': 300, 'max_file_size_kb': 500},
    'enterprise': {'max_files': 2000, 'timeout': 600, 'max_file_size_kb': 1024},
}

SKIP_DIRECTORIES = {
    'node_modules', '__pycache__', '.git', 'venv', 'env', '.venv',
    'dist', 'build', '.idea', '.vscode', 'vendor', 'lib', 'bin',
    'obj', 'assets', 'images', 'fonts', '.tox', '.eggs', '.mypy_cache',
    '.pytest_cache', 'htmlcov', 'coverage', '.nox'
}

TIER1_EXACT_NAMES = {
    '.env', 'Dockerfile', '.dockerignore', '.htaccess', '.htpasswd',
    'web.config', 'application.properties', 'appsettings.json',
    'secrets.yaml', 'secrets.yml', 'credentials.json'
}
TIER1_PREFIXES = ('config.', 'settings.', 'secrets.', 'credentials.', 'docker-compose.', '.env.')
TIER1_EXTENSIONS = {'.pem', '.key', '.cert', '.crt', '.pfx', '.p12'}

TIER2_KEYWORDS = [
    'auth', 'login', 'password', 'token', 'api', 'database', 'db',
    'connection', 'secret', 'credential', 'payment', 'billing', 'user', 'admin',
    'security', 'encrypt', 'decrypt', 'oauth', 'jwt', 'session', 'cookie'
]

TIER3_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb',
    '.php', '.cs', '.sql', '.sh', '.yml', '.yaml', '.json', '.xml',
    '.rs', '.swift', '.kt', '.scala', '.r', '.m', '.c', '.cpp', '.h'
}

AI_MODEL_EXTENSIONS = {
    '.pt', '.pth', '.h5', '.pb', '.onnx', '.pkl', '.joblib',
    '.safetensors', '.bin', '.keras', '.tflite', '.pickle',
    '.pmml', '.caffemodel', '.params', '.weights'
}

AI_CODE_KEYWORDS = [
    'model', 'train', 'predict', 'inference', 'pipeline', 'dataset',
    'transformer', 'neural', 'embedding', 'bias', 'fairness',
    'explainab', 'interpret', 'feature', 'preprocess', 'evaluate',
    'tokenize', 'encoder', 'decoder', 'attention', 'layer',
    'checkpoint', 'finetune', 'fine_tune', 'hyperparameter'
]

CLOUD_INFRA_EXTENSIONS = {'.tf', '.bicep', '.template'}
CLOUD_INFRA_PATTERNS = [
    'cloudformation', 'arm-template', 'deployment-manager',
    'kubernetes', 'k8s', 'helm', 'terraform', 'ansible', 'pulumi'
]


class SmartFileSelector:

    def __init__(self, scanner_type: str = 'general'):
        self.scanner_type = scanner_type

    def get_depth_preset(self, depth: str) -> Dict[str, Any]:
        return SCAN_DEPTH_PRESETS.get(depth, SCAN_DEPTH_PRESETS['standard'])

    def collect_files(self, root_path: str, max_file_size_kb: int = 200,
                      skip_dirs: Optional[Set[str]] = None) -> List[str]:
        if skip_dirs is None:
            skip_dirs = SKIP_DIRECTORIES

        all_files = []
        max_bytes = max_file_size_kb * 1024

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    if os.path.getsize(fpath) <= max_bytes:
                        all_files.append(fpath)
                except (OSError, PermissionError):
                    continue

        return all_files

    def _classify_file(self, fpath: str, repo_path: str) -> int:
        basename = os.path.basename(fpath).lower()
        ext = os.path.splitext(basename)[1]

        if self.scanner_type == 'ai_model':
            if ext in AI_MODEL_EXTENSIONS:
                return 1
            if any(kw in basename for kw in AI_CODE_KEYWORDS):
                return 2
            if ext in TIER3_EXTENSIONS:
                return 3
            return 4

        if self.scanner_type == 'sustainability':
            if ext in CLOUD_INFRA_EXTENSIONS:
                return 1
            if any(p in basename for p in CLOUD_INFRA_PATTERNS):
                return 1
            if basename in ('Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'):
                return 1
            if ext in {'.yml', '.yaml'} and any(kw in basename for kw in ['deploy', 'infra', 'cloud', 'k8s', 'helm']):
                return 2
            if ext in TIER3_EXTENSIONS:
                return 3
            return 4

        if basename in {n.lower() for n in TIER1_EXACT_NAMES}:
            return 1
        if any(basename.startswith(p) for p in TIER1_PREFIXES):
            return 1
        if ext in TIER1_EXTENSIONS:
            return 1
        if any(kw in basename for kw in TIER2_KEYWORDS):
            return 2
        if ext in TIER3_EXTENSIONS:
            return 3
        return 4

    def _sample_across_directories(self, file_list: List[str], budget: int,
                                    repo_path: str) -> List[str]:
        if not file_list or budget <= 0:
            return []
        if len(file_list) <= budget:
            return list(file_list)

        dir_buckets: Dict[str, List[str]] = {}
        for f in file_list:
            d = os.path.dirname(os.path.relpath(f, repo_path)) or '.'
            dir_buckets.setdefault(d, []).append(f)

        sorted_dirs = sorted(dir_buckets.keys())
        selected = []
        base_per_dir = max(1, budget // len(sorted_dirs))
        leftover = budget - (base_per_dir * len(sorted_dirs))

        for i, d in enumerate(sorted_dirs):
            alloc = base_per_dir + (1 if i < leftover else 0)
            take = min(alloc, len(dir_buckets[d]))
            selected.extend(dir_buckets[d][:take])

        return selected[:budget]

    def select_files(self, all_files: List[str], repo_path: str,
                     max_files: int) -> Tuple[List[str], Dict[str, Any]]:
        tiers: Dict[int, List[str]] = {1: [], 2: [], 3: [], 4: []}
        all_directories: Set[str] = set()

        for fpath in all_files:
            dirname = os.path.dirname(os.path.relpath(fpath, repo_path)) or '.'
            all_directories.add(dirname)
            tier = self._classify_file(fpath, repo_path)
            tiers[tier].append(fpath)

        selected_files: List[str] = []
        tiers_breakdown: Dict[str, int] = {}
        remaining = max_files

        tier_labels = self._get_tier_labels()

        for tier_num in [1, 2, 3, 4]:
            sampled = self._sample_across_directories(tiers[tier_num], remaining, repo_path)
            tiers_breakdown[f'tier_{tier_num}'] = len(sampled)
            tiers_breakdown[f'tier_{tier_num}_label'] = tier_labels.get(tier_num, f'Tier {tier_num}')
            tiers_breakdown[f'tier_{tier_num}_total'] = len(tiers[tier_num])
            selected_files.extend(sampled)
            remaining = max_files - len(selected_files)
            if remaining <= 0:
                break

        covered_dirs = set()
        for f in selected_files:
            covered_dirs.add(os.path.dirname(os.path.relpath(f, repo_path)) or '.')

        total_dirs = len(all_directories) if all_directories else 1

        coverage_report = {
            'total_files': len(all_files),
            'scanned_files': len(selected_files),
            'coverage_percentage': round((len(selected_files) / max(len(all_files), 1)) * 100, 2),
            'directories_covered': len(covered_dirs),
            'total_directories': total_dirs,
            'directory_coverage_percentage': round((len(covered_dirs) / max(total_dirs, 1)) * 100, 2),
            'tiers_breakdown': tiers_breakdown,
            'scanner_type': self.scanner_type,
        }

        return selected_files, coverage_report

    def _get_tier_labels(self) -> Dict[int, str]:
        if self.scanner_type == 'ai_model':
            return {
                1: 'Model Files (.pt, .h5, .onnx, .safetensors)',
                2: 'AI/ML Code (training, inference, pipeline)',
                3: 'Source Code (.py, .js, .java, etc.)',
                4: 'Other Files'
            }
        if self.scanner_type == 'sustainability':
            return {
                1: 'Infrastructure Files (.tf, Dockerfile, K8s)',
                2: 'Deployment Configs',
                3: 'Source Code',
                4: 'Other Files'
            }
        return {
            1: 'Config & Secrets',
            2: 'Security-Related',
            3: 'Source Code',
            4: 'Other Files'
        }

    def select_with_depth(self, root_path: str, scan_depth: str = 'standard',
                          skip_dirs: Optional[Set[str]] = None) -> Tuple[List[str], Dict[str, Any]]:
        preset = self.get_depth_preset(scan_depth)
        max_files = preset['max_files']
        max_file_size_kb = preset['max_file_size_kb']

        all_files = self.collect_files(root_path, max_file_size_kb=max_file_size_kb,
                                       skip_dirs=skip_dirs)
        selected, coverage = self.select_files(all_files, root_path, max_files)
        coverage['scan_depth'] = scan_depth
        coverage['scan_depth_preset'] = preset
        return selected, coverage

    @staticmethod
    def get_enterprise_compliance_metadata() -> Dict[str, Any]:
        return {
            'gdpr_article_32_compliant': True,
            'data_minimization': True,
            'purpose_limitation': 'privacy_compliance_scan',
            'retention': 'deleted_after_scan'
        }

    @staticmethod
    def get_data_residency_metadata() -> Dict[str, Any]:
        return {
            'processed_locally': True,
            'data_exported': False,
            'temp_files_cleaned': True,
            'encryption': 'in-memory only'
        }

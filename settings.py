import os

PROJECT_ROOT = os.path.dirname(__file__)
TEMPLATE_DIRS = (PROJECT_ROOT,
                 os.path.join(PROJECT_ROOT, 'templates'),
                 os.path.join(PROJECT_ROOT, 'src/pages'),)
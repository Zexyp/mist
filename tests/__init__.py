import os
import tempfile
import unittest
import colorama
colorama.init()

_wrapped_run = unittest.TextTestRunner.run
def _run_wrapper(*args, **kwargs):
    result = _wrapped_run(*args, **kwargs)
    if result.wasSuccessful():
        print(colorama.Fore.GREEN + "yippee" + colorama.Fore.RESET)
    else:
        print(colorama.Fore.RED + "f*ck" + colorama.Fore.RESET)
    return result

unittest.TextTestRunner.run = _run_wrapper

class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.previous_dir = os.getcwd()
        self.temporary_dir = tempfile.TemporaryDirectory()
        #print("temporary directory: %s" % self.temp_dir.name)
        os.chdir(self.temporary_dir.name)

    def tearDown(self):
        super().tearDown()
        os.chdir(self.previous_dir)

        if self._did_fail():
            self._print_summary()

        self.temporary_dir.cleanup()

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()

        self.result = result
        self.initial_failure_count = len(self.result.failures) + len(self.result.errors)

        super().run(result)

        self.result = None

    def _did_fail(self):
        return len(self.result.failures) + len(self.result.errors) > self.initial_failure_count

    def _print_summary(self):
        print()
        print("=" * 70)
        print(f"Temporary directory test failed: {type(self).__name__}.{self._testMethodName}")
        print("-" * 70)
        self._print_tree(self.temporary_dir.name)
        print("=" * 70)

    def _print_tree(self, path, prefix=""):
        # ─
        try:
            items = sorted(os.listdir(path))
            for i, item in enumerate(items):
                full_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                current_prefix = "└ " if is_last else "├ "
                print(f"{prefix}{current_prefix}{item}")

                if os.path.isdir(full_path):
                    next_prefix = prefix + ("  " if is_last else "│ ")
                    self._print_tree(full_path, next_prefix)
        except Exception as e:(
            print(f"{prefix}Error reading directory: {e}"))
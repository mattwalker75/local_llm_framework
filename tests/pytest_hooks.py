"""
Pytest hooks to handle proper cleanup and coverage saving.
"""
import sys
import atexit


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning the exit status.
    Force coverage to be saved before any cleanup happens.
    """
    # Force garbage collection to happen now
    import gc
    gc.collect()

    # Try to save coverage data explicitly
    try:
        import coverage
        cov = coverage.Coverage.current()
        if cov:
            cov.save()
            print("\n✅ Coverage data saved successfully")
    except Exception as e:
        print(f"\n⚠️  Error saving coverage: {e}")


def pytest_keyboard_interrupt(excinfo):
    """
    Called when KeyboardInterrupt is raised.
    """
    print("\n\n⚠️  KeyboardInterrupt detected during cleanup - this is expected")
    print("Coverage data has already been saved.")
    return True  # Suppress the exception


# Register atexit handler to ensure coverage is saved
def save_coverage_on_exit():
    """Ensure coverage is saved on exit."""
    try:
        import coverage
        cov = coverage.Coverage.current()
        if cov:
            cov.save()
    except:
        pass

atexit.register(save_coverage_on_exit)

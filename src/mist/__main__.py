import datetime
import logging
import sys
import traceback
import warnings


def main() -> int:
    # returns exit code
    logger = logging.getLogger("mist")
    start_time = datetime.datetime.now()
    try:
        with warnings.catch_warnings(record=True) as recorded_warnings:
            from mist import cli, log, MistError
            from mist.log import CustomHandler

            handler = CustomHandler()
            handler.setFormatter(logging.Formatter(
                fmt="[%(levelname)s][%(asctime)s][%(name)s]: %(message)s",
                datefmt="%Y.%m.%d-%H:%M:%S"
            ))

            logger.addHandler(handler)

            args = sys.argv[1:] # discard program name
            cli.run(args)
    except MistError as e:
        logger.error(str(e))
        logger.debug(e, exc_info=True)
        return 1
    except Exception as e:
        logger.fatal(f"{type(e).__name__}: {str(e)}")
        if isinstance(e, NotImplementedError):
            logger.fatal("lazy fuck detected")
        else:
            logger.fatal("unrecoverable error")
        logger.debug(e, exc_info=True)
        elapsed_time = datetime.datetime.now() - start_time
        logger.info(f"time wasted: {elapsed_time}")
        return 1
    finally:
        for w in recorded_warnings:
            logger.warning(w.message)
    return 0
    
if __name__ == "__main__":
    main()

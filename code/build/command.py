import argparse
import os
from types import SimpleNamespace

from dt_shell import DTCommandAbs, dtslogger, DTShell, UserError
from utils.dtproject_utils import DTProject


class DTCommand(DTCommandAbs):
    help = "Builds a Duckietown exercise into an image"

    @staticmethod
    def command(shell: DTShell, args, **kwargs):
        # Configure args
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-C",
            "--workdir",
            default=os.getcwd(),
            help="Directory containing the project to be built"
        )
        parser.add_argument(
            "-u",
            "--username",
            default=os.getlogin(),
            help="The docker registry username to use",
        )
        parser.add_argument(
            "--pull",
            default=False,
            action="store_true",
            help="Whether to pull the latest base image used by the Dockerfile",
        )
        parser.add_argument(
            "--recipe",
            default=None,
            help="Path to use if specifying a custom recipe",
        )
        parser.add_argument(
            "-b",
            "--base-tag",
            default=None,
            help="Docker tag for the base image." "Use when the base image is also a development version",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            default=False,
            action="store_true",
            help="Be verbose"
        )

        # Get pre-parsed or parse arguments
        parsed = kwargs.get("parsed", None)
        if not parsed:
            parsed, remaining = parser.parse_known_args(args=args)
            if remaining:
                dtslogger.warning(f"I do not know about these arguments: {remaining}")
        else:
            # combine given args with default values
            default_parsed = parser.parse_args(args=[""])
            for k, v in parsed.__dict__.items():
                setattr(default_parsed, k, v)
            parsed = default_parsed

        # Show dtproject info
        parsed.workdir = os.path.abspath(parsed.workdir)
        dtslogger.info("Project workspace: {}".format(parsed.workdir))
        shell.include.devel.info.command(shell, args)
        project = DTProject(parsed.workdir)

        # Make sure the project recipe is present
        if parsed.recipe is not None:
            if project.needs_recipe:
                recipe_dir: str = os.path.abspath(parsed.recipe)
                dtslogger.info(f"Using custom recipe from '{recipe_dir}'")
                project.set_recipe_dir(recipe_dir)
            else:
                raise UserError("This project does not support recipes")
        project.ensure_recipe_exists()

        # Try to update the project recipe
        if project.update_cached_recipe():
            dtslogger.info("Recipe updated!")

        # Build the project using 'devel buildx' functionality
        buildx_namespace: SimpleNamespace = SimpleNamespace(
            workdir=parsed.workdir,
            username=parsed.username,
            file=project.dockerfile,
            pull=parsed.pull,
            recipe=parsed.recipe,
            verbose=parsed.verbose,
            quiet=not parsed.verbose,
        )
        dtslogger.debug(f"Building with 'devel/buildx' using args: {args}")
        shell.include.devel.buildx.command(shell, [], parsed=buildx_namespace)

    @staticmethod
    def complete(shell, word, line):
        return []

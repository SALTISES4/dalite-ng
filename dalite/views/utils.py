import json
import logging
from typing import Any, List, Optional, Tuple, Union

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from dalite.views.errors import response_400

logger = logging.getLogger("reputation")


def get_json_params(
    req: HttpRequest,
    args: Optional[List[str]] = None,
    opt_args: Optional[List[str]] = None,
) -> Union[Tuple[List[Any], List[Any]], HttpResponse]:
    if args is None:
        args = []
    if opt_args is None:
        opt_args = []
    try:
        data = json.loads(req.body)
    except ValueError:
        return response_400(
            req,
            msg=_("Wrong data type was sent."),
            logger_msg=("The sent data wasn't in a valid JSON format."),
            log=logger.warning,
        )
    try:
        args = [data[arg] for arg in args]
        opt_args = [data.get(arg) for arg in opt_args]
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=(
                "The arguments {} were missing.".format(", ".join(e.args))
            ),
            log=logger.warning,
        )
    return args, opt_args


def get_query_string_params(
    req: HttpRequest,
    args: Optional[List[str]] = None,
    opt_args: Optional[List[str]] = None,
) -> Union[Tuple[List[Any], List[Any]], HttpResponse]:
    if args is None:
        args = []
    if opt_args is None:
        opt_args = []
    try:
        args = [req.GET[arg] for arg in args]
        opt_args = [req.GET.get(arg) for arg in opt_args]
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=(
                "The arguments {} were missing.".format(", ".join(e.args))
            ),
            log=logger.warning,
        )
    return args, opt_args


def with_json_params(
    args: Optional[List[str]] = None, opt_args: Optional[List[str]] = None
):
    def decorator(fct):
        def wrapper(
            req: HttpRequest, *args_, **kwargs_
        ) -> Union[Tuple[List[Any], List[Any]], HttpResponse]:
            all_args = get_json_params(req, args=args, opt_args=opt_args)
            if isinstance(all_args, HttpResponse):
                return all_args
            params = {
                **(
                    {arg: all_args[0][i] for i, arg in enumerate(args)}
                    if args
                    else {}
                ),
                **(
                    {
                        arg: all_args[1][i]
                        for i, arg in enumerate(opt_args)
                        if all_args[1][i] is not None
                    }
                    if opt_args
                    else {}
                ),
            }

            return fct(req, *args_, **kwargs_, **params)

        return wrapper

    return decorator


def with_query_string_params(
    args: Optional[List[str]] = None, opt_args: Optional[List[str]] = None
):
    def decorator(fct):
        def wrapper(
            req: HttpRequest, *args_, **kwargs_
        ) -> Union[Tuple[List[Any], List[Any]], HttpResponse]:
            all_args = get_query_string_params(
                req, args=args, opt_args=opt_args
            )
            if isinstance(all_args, HttpResponse):
                return all_args
            params = {
                **(
                    {arg: all_args[0][i] for i, arg in enumerate(args)}
                    if args
                    else {}
                ),
                **(
                    {
                        arg: all_args[1][i]
                        for i, arg in enumerate(opt_args)
                        if all_args[1][i] is not None
                    }
                    if opt_args
                    else {}
                ),
            }

            return fct(req, *args_, **kwargs_, **params)

        return wrapper

    return decorator

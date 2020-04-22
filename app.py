"""Web request handler and supporting components

These components include error handling, authorization, CORS,
logging, etc.
"""

import sys
import traceback
from typing import List

import requests
from fastapi import FastAPI, Query
from pydantic import AnyHttpUrl, BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

__version__ = '1.0.0'

app = FastAPI(
    title='City Events Service',
    description=(
        'Stateless service that provides events listed in Ticketmaster, '
        'filtered on the basis of city and other parameters'
    ),
    version=__version__,
)


class Links(BaseModel):
    self: AnyHttpUrl


class Event(BaseModel):
    name: str = None
    id: str
    url: str = None


class OutputModel(BaseModel):
    links: Links
    events: List[Event]


@app.get('/health_check', status_code=200, include_in_schema=False)
async def health_check():
    """Check health of the API"""
    return {'status': 'pass'}


def get_events_from_ticketmaster(api_key: str, city: str, postal_code: str = None) -> requests.Response:
    url = f'https://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}&city={city}'
    if postal_code:
        url = f'{url}&postalCode={postal_code}'
    return requests.get(url)


def construct_response(request: Request, resp_json):
    return OutputModel(
        links={
            'self': str(request.url)
        },
        events=[
            {
                'name': event.get('name'),
                'id': event.get('id'),
                'url': event.get('url'),
            }
            for event in resp_json['_embedded']['events']
        ]
    )


@app.get(
    '/city_events/',
    response_model=OutputModel,
    responses={
        401: {
            'description': 'Invalid APIKey',
            'content': {
                'application/json': {
                    'example': {
                        'detail': [{
                            'msg': 'string'
                        }],
                    },
                },
            },
        },

    },
)
async def get_city_events(
        request: Request,
        api_key: str = Query(
            ...,
            title='API key Query Parameter',
            description=(
                    'Ticketmaster API key. This key is passed directly to Ticketmaster'
            ),
        ),
        city: str = Query(
            ...,
            title='City Query Parameter URL',
            description=(
                    'City in which the events are to be found out'
            ),
        ),
        postal_code: str = Query(
            None,
            title='Postal code Query Parameter',
            description=(
                    'Postal code of the area where the events are to be found out'

            ),
        ),
):
    """Get the details of the events taking place in a particular city
    """
    resp = get_events_from_ticketmaster(api_key, city, postal_code)
    return construct_response(request, resp.json())


def log(msg):
    print(msg)
    sys.stdout.flush()


@app.exception_handler(ValidationError)
async def handle_central_exception(
        request: Request, exc: ValidationError
) -> JSONResponse:
    """Returns JSON error response for ValidationError"""
    log(str(exc))
    traceback.print_exc()
    return JSONResponse({'detail': [{'msg': str(exc)}]}, status_code=422)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8080)

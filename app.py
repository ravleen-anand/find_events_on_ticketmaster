from typing import List
import requests
from fastapi import FastAPI, Query
from pydantic import AnyHttpUrl, BaseModel
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
    events: List[Event] = None


def get_events_from_ticketmaster(api_key: str, city: str, postal_code: str = None) -> requests.Response:
    url = f'https://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}&city={city}'
    if postal_code:
        url = f'{url}&postalCode={postal_code}'
    return requests.get(url)


def construct_response(request: Request, resp_json):
    events = None
    if resp_json.get('_embedded'):
        events = [
            {
                'name': event.get('name'),
                'id': event.get('id'),
                'url': event.get('url'),
            }
            for event in resp_json['_embedded']['events']
        ]
    return OutputModel(
        links={
            'self': str(request.url)
        },
        events=events
    )


@app.get(
    '/city_events/',
    response_model=OutputModel,
    responses={
        401: {
            'description': 'Invalid API Key',
            'content': {
                'application/json': {
                    'example': {
                        'faultstring':'string',
                        'detail': {
                            'errorcode': 'string'
                        },
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
        search_id: int = Query(
            None,
            title='Search Id Query Parameter',
            description=(
                    'Id of the search performed. '
                    'This is used to demo ValidationError'

            ),
        ),
):
    """Get the details of the events taking place in a particular city
    """
    resp = get_events_from_ticketmaster(api_key, city, postal_code)
    if resp.status_code == 401:
        return JSONResponse(status_code=401, content=resp.json().get('fault'))
    return construct_response(request, resp.json())


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8080)

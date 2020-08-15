# AI Project: Video interpolation demo

This is basically set up for heroku-style deployment, although you don't have to (and probably shouldn't) use heroku for this. The built docker image is like 2.5gb so be careful of exceeding disk space. Probably a good idea to set resource limits as well otherwise people can dos you with big images. (Nginx in front of the app server _may_ reject requests that are too large, but don't count on it)

Due to the use of cpu-only pytorch the `requirements.txt` is tied to `python3.8/linux/x86_64`. If you want to run on some other combination of environment you need to tweak those requirements, you can find the links to pytorch wheels [here](https://download.pytorch.org/whl/torch_stable.html).

If you want to run locally just type `gunicorn app:app` after installing dependencies.

## Todo list

- ~~automatically resize frames to multiples of 64~~
- ~~automatically convert frames to 8bpc RGB removing alpha if it's there~~
- ~~automatically downsample frames to something reasonable~~
- Show on image the flow and weight map (this is already returned to the front end, check the console after processing)
- More detailed error messages

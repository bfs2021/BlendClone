import json
import shutil
import subprocess
from pathlib import Path

import pytest

APP_JS = Path(__file__).resolve().parents[1] / "web" / "app.js"

# Runs the real setVideo() and the speed <select> handler from web/app.js against
# video stubs that mirror the HTML media element rule: assigning a new source
# resets playbackRate to defaultPlaybackRate.
HARNESS = """
const setVideoSource = __SETVIDEO__;
const speedSource = __SPEED__;
function Video() { this._src = null; this.playbackRate = 1; this.defaultPlaybackRate = 1; }
Object.defineProperty(Video.prototype, 'src', {
  get() { return this._src; },
  set(value) { this._src = String(value); this.playbackRate = this.defaultPlaybackRate; },
});
Video.prototype.getAttribute = function (name) { return name === 'src' ? this._src : null; };
Video.prototype.removeAttribute = function (name) { if (name === 'src') this._src = null; };
Video.prototype.load = function () { this.playbackRate = this.defaultPlaybackRate; };
const listeners = {};
const nodes = {
  speed: { value: '1', addEventListener: (event, handler) => { listeners[event] = handler; } },
  'reference-video': new Video(),
  'remake-video': new Video(),
};
const $ = id => nodes[id];
const reference = nodes['reference-video'], remake = nodes['remake-video'];
eval(setVideoSource);
eval(speedSource);
nodes.speed.value = '0.5';
listeners.change();
setVideo('reference-video', '/api/jobs/a/files/source.mp4');
setVideo('remake-video', '/api/jobs/a/files/remake.mp4');
process.stdout.write(JSON.stringify({
  referenceRate: reference.playbackRate,
  remakeRate: remake.playbackRate,
  referenceDefault: reference.defaultPlaybackRate,
  remakeDefault: remake.defaultPlaybackRate,
}));
"""


def test_new_video_keeps_the_selected_playback_speed():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required to run the playback speed check")
    source = APP_JS.read_text(encoding="utf-8")
    set_video = source[
        source.index("function setVideo(") : source.index("function showProject(")
    ]
    speed_start = source.find("function applyPlaybackSpeed()")
    if speed_start == -1:
        speed_start = source.index("$('speed').addEventListener")
    speed_end = source.index("\n", source.index("$('speed').addEventListener"))
    speed = source[speed_start:speed_end]
    program = HARNESS.replace("__SETVIDEO__", json.dumps(set_video)).replace(
        "__SPEED__", json.dumps(speed)
    )
    completed = subprocess.run(
        [node, "-"],
        input=program,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result == {
        "referenceRate": 0.5,
        "remakeRate": 0.5,
        "referenceDefault": 0.5,
        "remakeDefault": 0.5,
    }, "a newly loaded source falls back to 1x while the speed menu still shows 0.5x"

import { Config } from "@remotion/cli/config";

// three.js needs WebGL in headless Chrome: ANGLE works with and without a GPU.
Config.setChromiumOpenGlRenderer("angle");
Config.setVideoImageFormat("jpeg");
Config.setConcurrency(1); // one WebGL context at a time is the stable choice

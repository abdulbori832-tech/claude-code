// One <Composition> per short: src/shorts/<name>/Short.tsx
import React from "react";
import { Composition } from "remotion";
import { Short as Mannequins, FRAMES as MANNEQUINS_FRAMES } from "./shorts/mannequins/Short";

export const Root: React.FC = () => (
  <>
    <Composition id="Mannequins" component={Mannequins} durationInFrames={MANNEQUINS_FRAMES} fps={30} width={1080} height={1920} />
  </>
);

export type CreatePanoramaRequest = {
  path: string;
};
export type SaveImageRequest = CreatePanoramaRequest & {
  path: string;
  image_topic: string;
  create_path: boolean;
};

export type CreatePanoramaResponse = {
  status: boolean;
  message: string;
};
export type SaveImageResponse = CreatePanoramaResponse;

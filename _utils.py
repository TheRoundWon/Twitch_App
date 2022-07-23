import ffmpeg

def create_mobile_video(logo_path, file_input, file_output, x_center, width, height):
    v1 = (
    ffmpeg
    .input(file_input)
    .crop(x_center, 0, width, height)
    .filter('eq', brightness=-1)
    )
    a1 = ffmpeg.input(file_input).audio
    v2 = (
        ffmpeg
        .input(file_input)
        .filter('scale', 614,-1)
    )

    overlay_file = ffmpeg.input(logo_path)

    (
        ffmpeg
        .concat(v1,a1, v=1, a=1)
        .overlay(overlay_file)
        .overlay(v2, y=300)
        .output(file_output)
        .run()
    )
def create_full_video(logo_path, file_input, file_output):
    overlay_file = ffmpeg.input(logo_path)
    a1 = ffmpeg.input(file_input).audio
    v1 = (
        ffmpeg
        .input(file_input)
        .overlay(overlay_file, x='main_w-overlay_w')
    )

    (
        ffmpeg
        .concat(v1, a1, v=1, a=1)
        .output(file_output)
        .run()
    )
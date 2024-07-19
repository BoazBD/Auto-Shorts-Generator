from random import randint
from sys import argv
from json import loads

from gtts import gTTS
import moviepy.editor as editor
from moviepy.video.fx.resize import resize
from moviepy.audio.fx.volumex import volumex

clip_durations = {"question": 10, "answer": 2.5}
full_question_duration = sum(clip_durations.values())


class Question:
    title: str
    answers: list[str]
    correct_answer: int

    def __init__(self):
        self.answers = []


def generate_speech(text, filename):
    tts = gTTS(text=text, lang="en")
    tts.save(filename)


def produce_short(
    questions: list[Question], background: str, music: str, font: str, output: str
):
    question_count = len(questions)

    background_duration = editor.VideoFileClip(background).duration
    background = resize(
        (
            editor.VideoFileClip(background)
            .cutout(0, randint(1, round(background_duration) - 65))
            .set_duration(full_question_duration * question_count)
            .set_position(("center", "center"))
        ),
        height=1920,
    )

    music_duration = editor.AudioFileClip(music).duration
    music = volumex(
        editor.CompositeAudioClip(
            [
                editor.AudioFileClip(music)
                .cutout(
                    0,
                    randint(
                        1, int(music_duration - full_question_duration * question_count)
                    ),
                )
                .set_end(full_question_duration * question_count)
            ]
        ),
        0.6,
    )

    clips = []
    speech_clips = []

    for question_index, question in enumerate(questions):
        question_text = (
            editor.TextClip(
                question["title"],
                fontsize=90,
                color="white",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(1080, None),
                font=font,
            )
            .set_position(("center", 0.03), relative=True)
            .set_start(question_index * full_question_duration)
            .set_duration(clip_durations["question"])
        )
        clips.append(question_text)

        # Generate speech for question text
        question_audio_filename = f"out/question_{question_index}.mp3"
        generate_speech(question["title"], question_audio_filename)
        question_audio_clip = editor.AudioFileClip(question_audio_filename).set_start(
            question_index * full_question_duration
        )
        speech_clips.append(question_audio_clip)

        answer_texts = [
            (
                editor.TextClip(
                    f"{list('ABCD')[i]} - {question['answers'][i]}",
                    fontsize=90,
                    color="white",
                    stroke_color="black",
                    stroke_width=2,
                    method="caption",
                    size=(1080, None),
                    font=font,
                )
                .set_position(("center", 0.35 + (i / 7)), relative=True)
                .set_start(question_index * full_question_duration)
                .set_duration(clip_durations["question"])
            )
            for i in range(len(question["answers"]))
        ]
        clips += answer_texts


        countdown_texts = [
            (
                editor.TextClip(
                    str(clip_durations["question"] - i),
                    fontsize=120,
                    color="white",
                    stroke_color="black",
                    stroke_width=2,
                    method="caption",
                    size=(1080, None),
                    font=font,
                )
                .set_start(question_index * full_question_duration + i)
                .set_duration(1)
                .set_position(("center", 0.87), relative=True)
            )
            for i in range(clip_durations["question"])
        ]
        clips += countdown_texts

        correct_answer_text = (
            editor.TextClip(
                question["answers"][question["correct"]],
                fontsize=120,
                color="#00ff00",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(1080, None),
                font=font,
            )
            .set_start(
                question_index * full_question_duration + clip_durations["question"]
            )
            .set_duration(clip_durations["answer"])
            .set_position("center")
        )
        clips.append(correct_answer_text)

    result: editor.CompositeVideoClip = editor.CompositeVideoClip(
        [background, *clips], size=(1080, 1920)
    ).set_audio(editor.CompositeAudioClip([music, *speech_clips]))

    result.write_videofile(
        output,
        fps=24,
        audio_codec="aac",
        threads=4,
        temp_audiofile="out/TEMP_trivia.mp4",
    )


if __name__ == "__main__":
    args = loads(argv[1])

    produce_short(
        questions=args["questions"],
        background=args["assets"]["background"],
        music=args["assets"]["music"],
        font=args["assets"]["font"],
        output=args["output"],
    )

# Real-Time-Traffic-Vehicle-Counting
A Modern Computer Vision Model whose main task is to gather infromation from Traffic videos. It counts the number of objects and also the type of objects that crosses a user defined line in the video and Gives the output as a CSV.

1) To get Started in the terminal install requirements from the requirements.txt file:

```pip install -r /path/to/requirements.txt```

2) In consumers.py add

    -> model_path(Path to yolo model)

    -> csv_path(Path to output CSV)

3) run the following commands and fill the details asked(Be sure to be in the project root folder)
   ```python manage.py makemigrations```
   ```python manage.py migrate```
   ```python manage.py createsuperuser```

4) run ```python manage.py runserver```

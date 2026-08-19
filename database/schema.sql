create table users(
user_id serial primary key,
email varchar(255) unique not null,
password_hash varchar(255) not null,
role varchar(20) not null check(role in ('student','teacher','parent','admin')),
created_at timestamp default current_timestamp
);


create table classes(
class_id serial primary key,
class_name varchar(20) not null,
section varchar(5) not null, 
academic_year varchar(9) not null,

unique(class_name, section, academic_year)
);

create table teachers(
teacher_id serial primary key,
user_id integer unique not null,
first_name varchar(50) not null,
last_name varchar(50) not null,
email varchar(100) unique not null,
phone varchar(15),
hire_date date,

foreign key(user_id)
references users(user_id)
on delete cascade
);

create table students(
student_id serial primary key,
user_id integer unique not null,
class_id integer not null,
roll_number integer not null,
first_name varchar(50) not null,
last_name varchar(50) not null,
date_of_birth date,
gender varchar(10),
admission_date date,
unique (class_id, roll_number),

foreign key(user_id)
references users(user_id)
on delete cascade,

foreign key(class_id)
references classes(class_id)
);

create table parents(
parent_id serial primary key,
user_id integer unique not null,
first_name varchar(50) not null,
last_name varchar(50) not null,
email varchar(100) unique not null,
phone varchar(15),

foreign key (user_id)
references users(user_id)
on delete cascade
);

create table parents_students(
parent_id integer not null,
student_id integer not null,
relationship varchar(20) not null,

primary key(parent_id, student_id),

foreign key(parent_id)
references parents(parent_id)
on delete cascade,

foreign key(student_id)
references students(student_id)
on delete cascade
);

create table subjects(
subject_id serial primary key,
subject_name varchar(100) unique not null,
subject_code varchar(20) unique not null
);

create table class_subjects(
class_subject_id serial primary key,
class_id integer not null,
subject_id integer not null,
teacher_id integer, 
unique(class_id, subject_id),
foreign key(class_id)
references classes(class_id)
on delete cascade,
foreign key(subject_id)
references subjects(subject_id)
on delete cascade,
foreign key(teacher_id)
references teachers(teacher_id)
on delete set null
);

create table attendance(
attendance_id serial primary key,
student_id integer not null,
attendance_date date not null,
status varchar(10) not null,
check(status in ('present','absent','late')),
unique(student_id, attendance_date),
foreign key(student_id)
references students(student_id)
on delete cascade
);

create table exams(
exam_id serial primary key,
exam_name varchar(50) not null,
academic_year varchar(9) not null,
start_date date not null,
end_date date not null
);

create table marks(
mark_id serial primary key,
student_id integer not null,
class_subject_id integer not null,
exam_id integer not null,
marks_obtained decimal(5,2) not null,
maximum_marks decimal(5,2) not null,

unique(student_id, class_subject_id, exam_id),

foreign key(student_id)
references students(student_id)
on delete cascade,

foreign key(class_subject_id)
references class_subjects(class_subject_id)
on delete cascade,

foreign key(exam_id)
references exams(exam_id)
on delete cascade
);

create table assignments(
assignment_id serial primary key,
class_subject_id integer not null,
title varchar(200) not null,
description text,
assigned_date date not null,
due_date date not null,

foreign key(class_subject_id)
references class_subjects(class_subject_id)
on delete cascade
);

create table announcements(
announcement_id serial primary key,
title varchar(200) not null,
message text not null,
posted_by integer not null,
posted_at timestamp default current_timestamp,

foreign key(posted_by)
references users(user_id)
);

create table timetable(
timetable_id serial primary key,
class_subject_id integer not null,
day_of_week varchar(10) not null
check(day_of_week in ('Monday', 'Tuesday', 'Wednesday','Thursday','Friday','Saturday')),
start_time time not null,
end_time time not null,

room_number varchar(20),

foreign key(class_subject_id)
references class_subjects(class_subject_id)
on delete cascade
);

alter table students
add constraint gender_check
check (gender in ('Male', 'Female', 'Other'));

alter table marks
add constraint marks_check
check (marks_obtained <= maximum_marks),
add constraint marks_positive_check
check(marks_obtained>=0);

alter table assignments
add constraint assignment_date_check
check(due_date>= assigned_date);

alter table exams
add constraint exam_date_check
check(end_date>=start_date);

alter table timetable
add constraint timetable_unique
unique(class_subject_id, day_of_week, start_time);

alter table parents_students
rename to parent_students;

alter table students
add column admission_number varchar(20) unique;




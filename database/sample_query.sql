DELETE FROM announcements;
DELETE FROM timetable;
DELETE FROM assignments;
DELETE FROM marks;
DELETE FROM attendance;
DELETE FROM parent_students;
DELETE FROM parents;
DELETE FROM students;
DELETE FROM class_subjects;
DELETE FROM exams;
DELETE FROM teachers;
DELETE FROM users;
DELETE FROM subjects;
DELETE FROM classes;

ALTER SEQUENCE announcements_announcement_id_seq RESTART WITH 1;
ALTER SEQUENCE timetable_timetable_id_seq RESTART WITH 1;
ALTER SEQUENCE assignments_assignment_id_seq RESTART WITH 1;
ALTER SEQUENCE marks_mark_id_seq RESTART WITH 1;
ALTER SEQUENCE attendance_attendance_id_seq RESTART WITH 1;
ALTER SEQUENCE parents_parent_id_seq RESTART WITH 1;

#--------------------------------------

-- ==========================
-- USERS (Admin + Teachers)
-- ==========================

INSERT INTO users (user_id, email, password_hash, role)
VALUES
(1,'admin@school.com','$2b$12$placeholder','admin'),
(2,'teacher1@school.com','$2b$12$placeholder','teacher'),
(3,'teacher2@school.com','$2b$12$placeholder','teacher'),
(4,'teacher3@school.com','$2b$12$placeholder','teacher'),
(5,'teacher4@school.com','$2b$12$placeholder','teacher'),
(6,'teacher5@school.com','$2b$12$placeholder','teacher'),
(7,'teacher6@school.com','$2b$12$placeholder','teacher'),
(8,'teacher7@school.com','$2b$12$placeholder','teacher'),
(9,'teacher8@school.com','$2b$12$placeholder','teacher'),
(10,'teacher9@school.com','$2b$12$placeholder','teacher'),
(11,'teacher10@school.com','$2b$12$placeholder','teacher');

-- ==========================
-- CLASSES
-- ==========================

INSERT INTO classes (class_id,class_name,section,academic_year) VALUES
(1,'1','A','2026-2027'),
(2,'2','A','2026-2027'),
(3,'3','A','2026-2027'),
(4,'4','A','2026-2027'),
(5,'5','A','2026-2027'),
(6,'6','A','2026-2027'),
(7,'7','A','2026-2027'),
(8,'8','A','2026-2027'),
(9,'9','A','2026-2027'),
(10,'10','A','2026-2027');

-- ==========================
-- SUBJECTS
-- ==========================

INSERT INTO subjects(subject_id,subject_name,subject_code) VALUES
(1,'English','ENG101'),
(2,'Mathematics','MAT101'),
(3,'Science','SCI101'),
(4,'Social Science','SST101'),
(5,'Hindi','HIN101'),
(6,'Computer Science','CSC101');

-- ==========================
-- TEACHERS
-- ==========================

INSERT INTO teachers
(teacher_id,user_id,first_name,last_name,email,phone,hire_date)
VALUES
(1,2,'Anjali','Sharma','teacher1@school.com','9876500001','2024-06-01'),
(2,3,'Rajesh','Verma','teacher2@school.com','9876500002','2024-06-01'),
(3,4,'Priya','Gupta','teacher3@school.com','9876500003','2024-06-01'),
(4,5,'Amit','Singh','teacher4@school.com','9876500004','2024-06-01'),
(5,6,'Neha','Patel','teacher5@school.com','9876500005','2024-06-01'),
(6,7,'Rohit','Mehta','teacher6@school.com','9876500006','2024-06-01'),
(7,8,'Kavita','Joshi','teacher7@school.com','9876500007','2024-06-01'),
(8,9,'Vivek','Kulkarni','teacher8@school.com','9876500008','2024-06-01'),
(9,10,'Pooja','Nair','teacher9@school.com','9876500009','2024-06-01'),
(10,11,'Sanjay','Iyer','teacher10@school.com','9876500010','2024-06-01');

-- ==========================
-- EXAMS
-- ==========================

INSERT INTO exams
(exam_id,exam_name,academic_year,start_date,end_date)
VALUES
(1,'Mid Term Examination','2026-2027','2026-09-15','2026-09-20'),
(2,'Final Examination','2026-2027','2027-02-20','2027-02-28');


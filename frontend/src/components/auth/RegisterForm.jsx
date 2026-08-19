import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import {registerStudent,} from "../../services/authService";

function RegisterForm() {
  const navigate = useNavigate();

  //const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    date_of_birth: "",
    gender: "",
    admission_number: "",
  });

  /*useEffect(() => {
  const fetchClasses = async () => {
    try {
      const data = await getClasses();
      console.log("Classes:", data);
      setClasses(data);
    } catch (error) {
      console.error(error);
    }
  };

  fetchClasses();
}, []);*/

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (form.password !== form.confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await registerStudent({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
        date_of_birth: form.date_of_birth,
        gender: form.gender,
        admission_number: form.admission_number,
      });

      alert("Registration Successful!");

      navigate("/");
    } catch (err) {
      alert(
        err.response?.data?.detail ||
          "Registration failed."
      );
    }

    setLoading(false);
  };

  return (
    <form className="register-form" onSubmit={handleSubmit}>
      <h2>Student Registration</h2>

      <div className="input-group">
        <label>First Name</label>

        <input
          name="first_name"
          value={form.first_name}
          onChange={handleChange}
          required
        />
      </div>

      <div className="input-group">
        <label>Last Name</label>

        <input
          name="last_name"
          value={form.last_name}
          onChange={handleChange}
          required
        />
      </div>

      <div className="input-group">
        <label>Email</label>

        <input
          type="email"
          name="email"
          value={form.email}
          onChange={handleChange}
          required
        />
      </div>

      <div className="input-group">
        <label>Password</label>

        <input
          type="password"
          name="password"
          value={form.password}
          onChange={handleChange}
          required
        />
      </div>

      <div className="input-group">
        <label>Confirm Password</label>

        <input
          type="password"
          name="confirmPassword"
          value={form.confirmPassword}
          onChange={handleChange}
          required
        />
      </div>

      <div className="input-group">
        <label>Date of Birth</label>

        <input
          type="date"
          name="date_of_birth"
          value={form.date_of_birth}
          onChange={handleChange}
          required
        />
      </div>

      <div className="input-group">
        <label>Gender</label>

        <select
          name="gender"
          value={form.gender}
          onChange={handleChange}
          required
        >
          <option value="">Select Gender</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </select>
      </div>

      <div className="input-group">
        <label>Admission Number</label>

        <input
          name="admission_number"
          value={form.admission_number}
          onChange={handleChange}
          required
        />
      </div>

      <button
  className="register-btn"
  type="submit"
  disabled={loading}
>
  {loading ? "Registering..." : "Register"}
</button>

<div className="register-link">
  <p>Already have an account?</p>
  <Link to="/">Login</Link>
</div>
    </form>
  );
}

export default RegisterForm;
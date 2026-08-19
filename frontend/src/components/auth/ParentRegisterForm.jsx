import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import { registerParent } from "../../services/authService";

function ParentRegisterForm() {

    const navigate = useNavigate();

    const [loading, setLoading] = useState(false);

    const [form, setForm] = useState({

        first_name: "",
        last_name: "",
        admission_number: "",
        date_of_birth: "",
        email: "",
        password: "",
        confirmPassword: "",

    });

    const handleChange = (e) => {

        setForm({
            ...form,
            [e.target.name]: e.target.value
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

            await registerParent({

                first_name: form.first_name,
                last_name: form.last_name,
                admission_number: form.admission_number,
                date_of_birth: form.date_of_birth,
                email: form.email,
                password: form.password,

            });

            alert("Parent Registration Successful!");

            navigate("/");

        }

        catch (err) {

            alert(
                err.response?.data?.detail ||
                "Registration failed."
            );

        }

        setLoading(false);

    };

    return (

<form className="login-form" onSubmit={handleSubmit}>

<h2>Parent Registration</h2>

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
<label>Admission Number</label>

<input
name="admission_number"
value={form.admission_number}
onChange={handleChange}
required
/>
</div>

<div className="input-group">
<label>Student Date of Birth</label>

<input
type="date"
name="date_of_birth"
value={form.date_of_birth}
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

<button disabled={loading}>
{loading ? "Registering..." : "Register"}
</button>

<div className="register-link">

<p>
Already have an account?
</p>

<Link to="/">
Login
</Link>

</div>

</form>

    );

}

export default ParentRegisterForm;
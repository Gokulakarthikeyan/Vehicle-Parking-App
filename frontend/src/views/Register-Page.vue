<template>
  <div class="register-wrapper d-flex align-items-center justify-content-center">
    <div class="container mt-5">
      <div class="card p-4 shadow-lg rounded-4">
        <h2 class="text-center mb-4 text-primary fw-bold">Create Account</h2>

        <form @submit.prevent="registerUser">
          <!-- Username (Email/Login) -->
          <div class="mb-3">
            <label for="username" class="form-label">Username (Email)</label>
            <input
              v-model="form.username"
              type="email"
              class="form-control"
              id="username"
              required
              placeholder="example@email.com"
            />
          </div>

          <!-- Password -->
          <div class="mb-3">
            <label for="password" class="form-label">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="form-control"
              id="password"
              required
              minlength="6"
              placeholder="Enter a strong password"
            />
          </div>

          <!-- Name -->
          <div class="mb-3">
            <label for="name" class="form-label">Full Name</label>
            <input
              v-model="form.name"
              type="text"
              class="form-control"
              id="name"
              placeholder="Your full name"
            />
          </div>

          <!-- Address -->
          <div class="mb-3">
            <label for="address" class="form-label">Address</label>
            <input
              v-model="form.address"
              type="text"
              class="form-control"
              id="address"
              placeholder="Street, city, etc."
            />
          </div>

          <!-- Pin Code -->
          <div class="mb-3">
            <label for="pin_code" class="form-label">Pin Code</label>
            <input
              v-model="form.pin_code"
              type="text"
              class="form-control"
              id="pin_code"
              placeholder="e.g. 600001"
            />
          </div>

          <!-- Submit -->
          <button type="submit" class="btn btn-primary w-100 fw-bold">
            Register
          </button>

          <!-- Login Link -->
          <div class="mt-3 text-center">
            <router-link to="/login" class="text-decoration-none">
              Already have an account? <span class="fw-semibold text-primary">Login</span>
            </router-link>
          </div>
        </form>

        <!-- Feedback Messages -->
        <div v-if="message" class="alert mt-3" :class="success ? 'alert-success' : 'alert-danger'">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      form: {
        username: '',
        password: '',
        name: '',
        address: '',
        pin_code: ''
      },
      message: '',
      success: false
    }
  },
  methods: {
    async registerUser() {
      this.message = ''
      this.success = false

      try {
        const res = await axios.post('http://localhost:5000/api/register', this.form)
        this.message = res.data.message || 'Registration successful!'
        this.success = true

        // Small delay before redirect
        setTimeout(() => {
          this.$router.push('/login')
        }, 1500)
      } catch (err) {
        if (err.response && err.response.data && err.response.data.message) {
          this.message = err.response.data.message
        } else {
          this.message = 'Registration failed. Please try again.'
        }
        this.success = false
      }
    }
  }
}
</script>

<style scoped>
.register-wrapper {
  min-height: 100vh;
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card {
  border: none;
  border-radius: 1rem;
  background: #ffffff;
}

.form-control {
  border-radius: 0.5rem;
}

.btn-primary {
  background-color: #007bff;
  border: none;
  transition: 0.3s ease;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.alert {
  font-weight: 500;
  text-align: center;
}
</style>

<template>
  <div class="login-wrapper d-flex align-items-center justify-content-center">
    <div class="login-box shadow-lg p-4 bg-white rounded">
      <h2 class="text-center mb-4 text-primary">Vehicle Parking App</h2>
      
      <form @submit.prevent="loginUser">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input
            v-model="username"
            type="text"
            id="username"
            class="form-control"
            required
          />
        </div>

        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input
            v-model="password"
            type="password"
            id="password"
            class="form-control"
            required
          />
        </div>

        <button type="submit" class="btn btn-primary w-100">Login</button>
        <p class="text-danger mt-2 text-center" v-if="error">{{ error }}</p>
      </form>

      <p class="text-center mt-3">
        New user? 
        <router-link to="/register">Register here</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      username: "",
      password: "",
      error: "",
    };
  },
  methods: {
    async loginUser() {
      this.error = "";

      try {
        const res = await axios.post("http://localhost:5000/api/login", {
          username: this.username,
          password: this.password,
        });

        if (res.data.success) {
          // ✅ Save token for future authenticated requests
          localStorage.setItem("authToken", res.data.token);
          localStorage.setItem("username", res.data.username);
          localStorage.setItem("role", res.data.role);

          // Redirect based on role
          if (res.data.role === "admin") {
            this.$router.push("/admin/dashboard");
          } else {
            this.$router.push("/user/dashboard");
          }
        } else {
          this.error = "Invalid username or password";
        }
      } catch (err) {
        this.error = "Server error or invalid credentials.";
      }
    },
  },
};
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  background: linear-gradient(to right, #4facfe, #00f2fe);
  background-size: cover;
  background-position: center;
}

.login-box {
  width: 100%;
  max-width: 400px;
  background-color: white;
}
</style>

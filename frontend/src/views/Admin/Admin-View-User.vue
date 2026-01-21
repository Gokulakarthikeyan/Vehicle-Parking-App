<template>
    <nav class="navbar navbar-expand-lg login-wrapper mb-4">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">Admin Dashboard</a>
        <ul class="navbar-nav ms-auto">
          <li class="nav-item"><router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/admin/view-user">View user</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/admin/search">Search</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/admin/summary">Summary</router-link></li>
          <li class="nav-item"><a class="nav-link" href="#" @click.prevent="logout">Logout</a></li>
        </ul>
      </div>
    </nav>

    <div class="container admin-dashboard">
      <h1 class="mb-4">User List</h1>
      <div v-if="users.length === 0" class="alert alert-info">
        No users found.
      </div>

      <table v-else class="table table-striped mt-3">
        <thead>
          <tr>
            <th>S.No.</th>
            <th>Name</th>
            <th>Username</th>
            <th>Address</th>
            <th>Pin Code</th>
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, index) in users" :key="user.id">
            <td>{{ index + 1 }}</td>
            <td>{{ user.name }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.address }}</td>
            <td>{{ user.pin_code }}</td>
            <td>{{ user.role }}</td>
          </tr>
        </tbody>
      </table>

    </div>
</template>

<script>
import axios from "axios";
import { useToast } from "vue-toastification";

export default {
  name: "UserList",
  data() {
    return {
      users: [],
      toast: useToast(),
    };
  },
  methods: {
    async fetchUsers() {
      try {
        const token = localStorage.getItem("authToken");
        const response = await axios.get("http://127.0.0.1:5000/api/admin/users", {
          headers: { Authorization: `Bearer ${token}` },
        });
        this.users = response.data;
        this.toast.success("User list loaded!");
      } catch (error) {
        console.error("Failed to fetch users:", error.response?.data || error.message);
        if (error.response?.status === 401) {
          this.toast.error("Unauthorized. Please log in again.");
          this.logout();
        } else {
          this.toast.error("Error loading users.");
        }
      }
    },
    logout() {
      localStorage.removeItem("authToken");
      this.toast.info("Logged out.");
      this.$router.push("/login");
    },
  },
  mounted() {
    this.fetchUsers();
  },
};
</script>

<style scoped>
.admin-dashboard {
  padding: 2rem 1rem;
}
.table {
  width: 100%;
  margin-top: 1rem;
}
.login-wrapper {
  background: linear-gradient(to right, #4facfe, #00f2fe);
}
</style>

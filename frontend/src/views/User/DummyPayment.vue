<template>
  <div class="container mt-5 text-center">
    <h2>Dummy Payment Portal</h2>
    <p>Amount: ₹{{ amount }}</p>

    <button class="btn btn-success mt-3" @click="paySuccess">
      Pay Success
    </button>

    <button class="btn btn-danger mt-3 ms-2" @click="payFail">
      Pay Failed
    </button>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      amount: this.$route.query.amount,
      reservation_id: this.$route.query.reservation_id
    };
  },
  methods: {
    async paySuccess() {
      await axios.post("http://localhost:5000/api/payment/confirm", {
        reservation_id: this.reservation_id
      });
      alert("Payment Successful!");
      this.$router.push("/user/dashboard");
    },
    payFail() {
      alert("Payment Failed!");
      this.$router.push("/user/dashboard");
    }
  }
};
</script>

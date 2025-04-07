"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

const Home = () => {
  const router = useRouter();

  useEffect(() => {
    router.push("/simulation"); // Redirect to /simulation
  }, [router]);

  return null; // Optionally, you can add a loading spinner or message here
};

export default Home;

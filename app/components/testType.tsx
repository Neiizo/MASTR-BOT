const testType = (temp : any) => {
  console.log("val is ", temp);
  console.log("Type of val is ", typeof temp);
  console.log("Testing with number", typeof temp === "number");
  console.log("Testing with string", typeof temp === "string");
  console.log("Testing if it counts as an array", Array.isArray(temp));
  
  if (Array.isArray(temp)) {
    console.log("It is an array");
    console.log("Testing first element");
    testType(temp[0]);
  }
}

export default testType
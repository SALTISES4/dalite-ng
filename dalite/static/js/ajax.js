export function getCsrfToken() {
  return document
    .getElementsByName("csrfmiddlewaretoken")[0]
    .getAttribute("value");
}

export function buildReq(data, method) {
  if (method.toLowerCase() === "get") {
    return {
      method: method.toUpperCase(),
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
    };
  } else if (method.toLowerCase() === "post") {
    const body = data ? JSON.stringify(data) : "";
    return {
      method: method.toUpperCase(),
      body: body,
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
    };
  } else {
    throw Error(`Method ${method} not implemented yet.`);
  }
}

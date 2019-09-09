import { init as initMessages } from "./dashboard/messages.js";

/********/
/* init */
/********/

export async function init(data) {
  initMessages({
    urls: {
      daliteMessages: data.urls.dalite_messages,
      removeDaliteMessage: data.urls.remove_dalite_message,
      saltiseImage: data.urls.saltise_image,
    },
  });
}

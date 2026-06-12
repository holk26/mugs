import { NodePlatform } from "@storecraft/core/platform/node"
import { SQLite } from "@storecraft/database-sqlite"
import { NodeLocalStorage } from "@storecraft/core/storage/node"
import { App } from "@storecraft/core"
import { PostmanExtension } from "@storecraft/core/extensions/postman"

export const app = new App({
  general_store_name: "core",
  auth_admins_emails: ["homero9726@gmail.com"],
  general_store_support_email:
    "homero9726@gmail.com",
})
  .withPlatform(new NodePlatform({}))
  .withDatabase(new SQLite({
    filepath: "data.sqlite",
  }))
  .withStorage(new NodeLocalStorage("storage"))
  .withExtensions({
    postman: new PostmanExtension(),
  })
  .init()

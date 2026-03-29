# Topics
[1. LLM Work Flows](https://github.com/adityaiyer7/blogs/tree/master/llm_work_flows)

## Authoring Blog Posts

This repository contains a simplified directory structure for generating blog content using Quarto under `blogposts/`.

To create a new blog post, use the included helper script from the root of the repository:

```bash
./create_post.sh "my-post-name"
```
Or to automatically import an existing Markdown draft:
```bash
./create_post.sh "my-post-name" "/path/to/your/draft.md"
```

**What the script does:**
1. It creates a new folder for the post under `blogposts/posts/<post-slug>/`.
2. It sets up an isolated assets folder `assets/imgs/`.
3. If you provided a path to a draft `.md` file, it copies the `.md` file into the folder as `draft.md` (to preserve your original work) and automatically appends the contents into an `index.qmd` file with pre-filled YAML front matter.
4. If no `.md` draft is provided, it simply creates a starter `index.qmd` file with pre-filled front matter.

Inside your newly generated `index.qmd`, you can include manually copied images using the relative path `![](assets/imgs/your-image.png)`.

### Deleting Blog Posts

If you want to fully delete a post from your repository, do **not** just delete the source folder, as the generated `.html` files will be left behind in the `docs/` folder. Instead, use the included deletion script:

```bash
./delete_post.sh "my-post-name"
```
Or run interactively:
```bash
./delete_post.sh
```

**What the script does:**
1. It safely asks for confirmation before deleting anything.
2. It permanently deletes your source folder `blogposts/posts/<post-slug>/`.
3. It permanently deletes any generated, orphaned `.html` output files in `blogposts/docs/posts/<post-slug>/`.

After deleting a post, just run `quarto render` in the `blogposts/` directory to instantly update your site's index.

## Previewing and Publishing

To see a live, auto-updating preview of your blog locally while you write:
```bash
cd blogposts
quarto preview
```

When you are ready to publish and build all the raw HTML files for hosting:
```bash
cd blogposts
quarto render
```

<details>
<summary>Repo Notes</summary>

`llm_work_flows` and `llm-from-scratch` are deprecated and no longer maintained. They were originally created for a Substack blog that is no longer being run, and the blog has shifted to the `blogposts` folder.
</details>

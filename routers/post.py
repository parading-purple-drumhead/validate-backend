from operator import itemgetter
from fastapi import APIRouter, HTTPException, Request
from routers import db
from models import Post, Comment

router = APIRouter()


def user_verified(user_id: str, category: str):
    category_ref = db.collection(u"categories").document(category)
    category_data = category_ref.get().to_dict()

    if user_id not in category_data.keys():
        return False

    user_comments = category_data[user_id]
    if len(user_comments) == 0:
        return False

    averages = []

    for comment_id in user_comments.keys():
        ratings = user_comments[comment_id]
        if len(ratings) == 0:
            return False
        averages.append(round(sum(ratings.values())/len(ratings), 1))

    averageOfAverages = round(sum(averages)/len(averages), 1)
    n = len(user_comments)

    trust = ((1 - (1/(n+1))) * averageOfAverages) / 5 * 100

    if n < 10:
        if trust < 80:
            verified = False
        else:
            verified = True
    elif n < 50:
        if trust < 75:
            verified = False
        else:
            verified = True
    elif n < 100:
        if trust < 70:
            verified = False
        else:
            verified = True

    return True


@router.get("/")
def get_posts(request: Request, my_posts: bool | None = None):
    try:
        current_uid = request.headers.get("uid")

        if my_posts:
            posts_ref = db.collection(u"posts").where(
                "authorId", "==", current_uid)
        else:
            posts_ref = db.collection(u"posts")

        posts_data = posts_ref.get()
        if len(posts_data) == 0:
            return []

        unsorted_posts = []

        for post in posts_data:
            post_dict = post.to_dict()
            post_dict["id"] = post.id

            author_ref = db.collection(
                u"users").document(post_dict["authorId"])
            author = author_ref.get().to_dict()
            post_dict["author"] = author["name"]
            post_dict["profilePic"] = author["profilePic"]

            comments_ref = db.collection(u"posts").document(
                post.id).collection("comments")
            comments_data = comments_ref.get()

            if len(comments_data) > 0:
                unsorted_comments = []
                for comment in comments_data:
                    comment_dict = comment.to_dict()
                    comment_dict["id"] = comment.id

                    author_ref = db.collection(
                        u"users").document(comment_dict["authorId"])
                    author = author_ref.get().to_dict()
                    comment_dict["author"] = author["name"]
                    comment_dict["profilePic"] = author["profilePic"]

                    if len(comment_dict["ratings"]) > 0:
                        if current_uid in comment_dict["ratings"].keys():
                            comment_dict["userRating"] = comment_dict["ratings"][current_uid]
                        else:
                            comment_dict["userRating"] = 0
                        comment_dict["rating"] = round(
                            (sum(comment_dict["ratings"].values())/len(comment_dict["ratings"])), 2)
                        comment_dict["numberOfRatings"] = len(
                            comment_dict["ratings"])
                    else:
                        comment_dict["rating"] = 0
                        comment_dict["numberOfRatings"] = 0
                        comment_dict["userRating"] = 0

                    comment_dict["verified"] = user_verified(
                        comment_dict["authorId"], post_dict["category"])

                    unsorted_comments.append(comment_dict)

                comments = sorted(unsorted_comments, key=itemgetter(
                    'numberOfRatings'), reverse=True)

                if len(comments) > 0:
                    post_dict["comments"] = [comments[0]]
                else:
                    post_dict["comments"] = comments

            else:
                post_dict["comments"] = []

            post_dict["details"] = False

            unsorted_posts.append(post_dict)
            posts = sorted(unsorted_posts, key=itemgetter(
                'date'), reverse=True)

        return posts

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{post_id}/")
def get_single_post(post_id: str, request: Request):
    try:
        current_uid = request.headers.get("uid")
        post_ref = db.collection(u"posts").document(post_id)
        post_data = post_ref.get()
        if not post_data.exists:
            raise Exception("Post does not exist")
        post = post_data.to_dict()

        post["id"] = post_data.id

        author_ref = db.collection(u"users").document(post["authorId"])
        author = author_ref.get().to_dict()
        post["author"] = author["name"]
        post["profilePic"] = author["profilePic"]

        comments_ref = db.collection(u"posts").document(
            post_data.id).collection("comments")
        comments_data = comments_ref.get()
        unsorted_comments = []
        for comment in comments_data:
            comment_dict = comment.to_dict()
            comment_dict["id"] = comment.id

            author_ref = db.collection(
                u"users").document(comment_dict["authorId"])
            author = author_ref.get().to_dict()
            comment_dict["author"] = author["name"]
            comment_dict["profilePic"] = author["profilePic"]

            if len(comment_dict["ratings"]) > 0:
                if current_uid in comment_dict["ratings"].keys():
                    comment_dict["userRating"] = comment_dict["ratings"][current_uid]
                else:
                    comment_dict["userRating"] = 0
                comment_dict["rating"] = round(
                    (sum(comment_dict["ratings"].values())/len(comment_dict["ratings"])), 2)
                comment_dict["numberOfRatings"] = len(comment_dict["ratings"])
            else:
                comment_dict["rating"] = 0
                comment_dict["numberOfRatings"] = 0

            comment_dict["verified"] = user_verified(
                comment_dict["authorId"], post["category"])

            unsorted_comments.append(comment_dict)

        comments = sorted(unsorted_comments, key=itemgetter(
            'numberOfRatings'), reverse=True)

        post["comments"] = comments
        post["details"] = True

        return post

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/add")
def add_post(post: Post):
    try:
        posts_ref = db.collection(u"posts")
        new_post_ref = posts_ref.add(dict(post))

        user_ref = db.collection(u"users").document(post.authorId)
        user_data = user_ref.get().to_dict()
        user_data["postsCreated"].append(new_post_ref[1].id)
        user_ref.update({u"postsCreated": user_data["postsCreated"]})

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{post_id}/comment/add")
def add_comment(post_id: str, comment: Comment, request: Request):
    try:
        category = request.headers.get("category")
        comments_ref = db.collection(u"posts").document(
            post_id).collection(u"comments")
        new_comment_ref = comments_ref.add(dict(comment))

        comment_dict = dict(comment)
        comment_dict["id"] = new_comment_ref[1].id

        user_ref = db.collection(u"users").document(comment.authorId)
        user_dict = user_ref.get().to_dict()

        comment_dict["author"] = user_dict["name"]
        comment_dict["profilePic"] = user_dict["profilePic"]
        comment_dict["rating"] = 0
        comment_dict["numberOfRatings"] = 0
        comment_dict["userRating"] = 0
        comment_dict["verified"] = user_verified(comment.authorId, category)

        return comment_dict

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{post_id}/comment/{comment_id}/rate")
def rate_comment(post_id: str, comment_id: str, comment: Comment):
    try:
        post_ref = db.collection(u"posts").document(post_id)
        comment_ref = post_ref.collection(u"comments").document(comment_id)

        comment_ref.update(dict(comment))

        post_data = post_ref.get().to_dict()
        categories_ref = db.collection(u"categories")
        category_ref = categories_ref.document(post_data["category"])
        category_data = category_ref.get()

        if category_data.exists:
            category_dict = category_data.to_dict()
            if not category_dict[comment.authorId]:
                category_dict[comment.authorId] = {comment_id: comment.ratings}
            else:
                category_dict[comment.authorId][comment_id] = comment.ratings
            category_ref.update(category_dict)

        else:
            category_data = {comment.authorId: comment.ratings}
            categories_ref.add(
                category_data, document_id=post_data["category"])

        return {"message": "Comment rated successfully"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

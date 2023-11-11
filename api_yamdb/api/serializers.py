from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from reviews.constants import MIN_SCORE_VALUE, MAX_SCORE_VALUE
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    '''Для классов Регистрации и Проверки токена не нужно общение с БД, нужно переопределить родительский класс.
Так же смотри замечание в модели про валидацию и про длину полей, это касается всех сериалайзеров для Пользователя.'''

    class Meta:
        model = User
        fields = (
            'username', 'email'
        )

    def validate(self, data):
        if data.get('username') == 'me': # Этого мало, нужна проверка на регулярку, см. в модели.
                                         # Тоже самое для всех сериализаторов пользователя.
            raise serializers.ValidationError('Недопустимое имя пользователя')
        if User.objects.filter(email=data.get('email')):
            raise serializers.ValidationError('Такой e-mail уже есть')
        if User.objects.filter(username=data.get('username')):
            raise serializers.ValidationError('Такой пользователь уже есть')
        return data


class UserRecieveTokenSerializer(serializers.Serializer):
    username = serializers.RegexField(regex=r'^[\w.@+-]+$',
                                      max_length=150,
                                      required=True)
    confirmation_code = serializers.CharField(max_length=254,
                                              required=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role')

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError('Недопустимое имя пользователя')
        return username


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Category


class DetailedTitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(many=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'category', 'genre')

    def get_rating(self, obj):
        reviews = Review.objects.filter(title=obj.id)
        if reviews:
            total_score = sum(review.score for review in reviews)
            return total_score / len(reviews)
        return None


class CreateTitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=Category.objects.all(),
                                            slug_field='slug')
    genre = serializers.SlugRelatedField(queryset=Genre.objects.all(),
                                         many=True,
                                         slug_field='slug')

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'category', 'genre')
        read_only_fields = ('rating',)
    
    '''Так у нас вывод информации после Пост запроса будет не по ТЗ,
    нужно добавить сюда метод который позволит выводить информацию как при гет запросе.
    Не путаем нужно написать всего один метод.
    Нужна валидация поля Жанра, у нас по ТЗ это поля обязательное, если сейчас
    передать пустой список через Postman, то Произведение создастся вообще без Жанров'''


class ReviewSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True,
                              default=serializers.CurrentUserDefault())
    score = serializers.IntegerField(max_value=MAX_SCORE_VALUE,
                                     min_value=MIN_SCORE_VALUE)

    class Meta:
        fields = '__all__'
        model = Review
        extra_kwargs = { # Так может не сработать
            'score':
            {'error_messages':
                {'max_value': ('Нельзя поставить больше десятки'),
                 'min_value': ('Нельзя поставить меньше единицы')}}
        }

    def validate(self, data):
        if self.context['request'].method == 'POST':
            author_id = self.context['request'].user.id
            title_id = self.context['view'].kwargs.get('title_id')
            review = Review.objects.filter(author_id=author_id,
                                           title_id=title_id)
            if review.exists():
                raise serializers.ValidationError(
                    'Неуникальная пара Автор-Отзыв')
            return data


class CommentSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        fields = '__all__'
        model = Comment
        read_only_fields = ('review',)
